"""Score a finished eval workspace (a Swift package) against its task.

Usage: python3 -I evals/score.py <task_dir> <workspace_dir>  → prints JSON

Metrics:
  build_ok, source_warnings      iOS 26.5 simulator build; warnings located in Sources/
  hidden_passed / hidden_total   hidden Swift Testing suite `HiddenTests`
  lint_violations (by rule)      harness .swiftlint.yml with --strict, Sources/ only
  max_complexity                 highest SwiftLint cyclomatic complexity of any function
  patterns                       task-specific regex counts (forbidden / required / metric)
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SWIFTLINT = (ROOT / "tools/lint/.build/artifacts/swiftlintplugins/SwiftLintBinary"
             / "SwiftLintBinary.artifactbundle/macos/swiftlint")
SIM_RUNTIME = "iOS 26.5"
SIM_NAME = "iPhone 17"


def simulator_udid() -> str:
    devices = json.loads(subprocess.run(
        ["xcrun", "simctl", "list", "devices", "available", "-j"],
        capture_output=True, text=True, check=True).stdout)["devices"]
    for runtime, entries in devices.items():
        if runtime.endswith(SIM_RUNTIME.replace(" ", "-").replace(".", "-")):
            for device in entries:
                if device["name"] == SIM_NAME:
                    return device["udid"]
    raise RuntimeError(f"No {SIM_NAME} simulator for {SIM_RUNTIME}")


def swift_sources(workspace: pathlib.Path) -> list[pathlib.Path]:
    return sorted((workspace / "Sources").rglob("*.swift"))


def run(cmd: list[str], workspace: pathlib.Path, log_name: str) -> str:
    proc = subprocess.run(cmd, cwd=workspace, capture_output=True, text=True, timeout=1800)
    log = proc.stdout + proc.stderr
    (workspace / log_name).write_text(log)
    return log


def source_warnings(log: str, workspace: pathlib.Path) -> set[str]:
    sources_dir = str((workspace / "Sources").resolve())
    return {line.strip() for line in log.splitlines()
            if " warning: " in line and sources_dir in str(pathlib.Path(line.split(":")[0]).resolve())}


def hidden_results(log: str) -> tuple[int, int]:
    """(passed, failed) test functions, from Swift Testing's run summary and its ✘ lines.
    Per-test ✔ lines are unreliable: parameterized tests print "with N test cases", and
    parallel output can interleave lines."""
    totals = re.findall(r"Test run with (\d+) tests?", log)
    if not totals:
        return 0, 0
    failed = len(set(re.findall(r"✘ Test (\w+)\(", log)))
    return int(totals[-1]) - failed, failed


def run_tests(task: dict, workspace: pathlib.Path) -> dict:
    """Build + hidden tests on the iOS simulator; or, for test_host=macos (e.g. Keychain,
    which needs an entitlement in simulator package tests), an iOS build plus `swift test`."""
    module = task["module"]
    xcodebuild = ["xcodebuild", "-scheme", module,
                  "-destination", f"platform=iOS Simulator,id={simulator_udid()}",
                  "-derivedDataPath", str(workspace / ".derived")]
    if task.get("test_host") == "macos":
        build_log = run([*xcodebuild, "build"], workspace, ".score-xcodebuild.log")
        test_log = run(["swift", "test", "--filter", "HiddenTests"], workspace, ".score-swifttest.log")
        build_ok = "** BUILD SUCCEEDED **" in build_log
    else:
        build_log = test_log = run([*xcodebuild, "test", f"-only-testing:{module}Tests/HiddenTests"],
                                   workspace, ".score-xcodebuild.log")
        build_ok = None
    warnings = source_warnings(build_log, workspace)
    passed, failed = hidden_results(test_log)
    if build_ok is None:
        # Tests only run (pass or fail) when the package and hidden suite compiled.
        build_ok = (passed + failed) > 0
    return {"build_ok": build_ok, "source_warnings": len(warnings),
            "warning_lines": sorted(warnings)[:20],
            "hidden_passed": passed, "hidden_total": task["hidden_tests"]}


def lint(workspace: pathlib.Path, config_text: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        shutil.copytree(workspace / "Sources", work / "Sources")
        (work / ".swiftlint.yml").write_text(config_text)
        return subprocess.run([str(SWIFTLINT), "lint", "--strict", "--quiet"],
                              cwd=work, capture_output=True, text=True).stdout


def lint_metrics(workspace: pathlib.Path) -> dict:
    out = lint(workspace, (ROOT / ".swiftlint.yml").read_text())
    by_rule: dict[str, int] = {}
    for rule in re.findall(r"\((\w+)\)$", out, re.M):
        by_rule[rule] = by_rule.get(rule, 0) + 1
    cc_config = ("included: [Sources]\nonly_rules: [cyclomatic_complexity]\n"
                 "cyclomatic_complexity:\n  warning: 1\n  error: 1000\n")
    scores = [int(n) for n in re.findall(r"complexity is (\d+)", lint(workspace, cc_config))]
    return {"lint_violations": sum(by_rule.values()), "lint_by_rule": by_rule,
            "max_complexity": max(scores, default=1)}


def pattern_metrics(task: dict, workspace: pathlib.Path) -> dict:
    text = "\n".join(p.read_text() for p in swift_sources(workspace))
    count = lambda rx: len(re.findall(rx, text, re.M))  # noqa: E731
    return {
        "forbidden": {name: count(rx) for name, rx in task.get("forbidden", {}).items()},
        "required_missing": [name for name, rx in task.get("required", {}).items() if not count(rx)],
        "metrics": {name: count(rx) for name, rx in task.get("metrics", {}).items()},
        "source_lines": sum(1 for line in text.splitlines() if line.strip()),
    }


def score(task_dir: pathlib.Path, workspace: pathlib.Path) -> dict:
    task = json.loads((task_dir / "task.json").read_text())
    tests_dir = workspace / "Tests" / f"{task['module']}Tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    for hidden in (task_dir / "hidden").glob("*.swift"):
        shutil.copy(hidden, tests_dir / hidden.name)
    return {**run_tests(task, workspace), **lint_metrics(workspace), **pattern_metrics(task, workspace)}


if __name__ == "__main__":
    print(json.dumps(score(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])), indent=2))
