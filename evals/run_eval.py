"""Run headless agent evals: tasks × configs × repeats, then score each workspace.

Usage:
  python3 -I evals/run_eval.py --configs none,upstream --repeats 2 [--tasks pricing,token] [--dry-run]

Each run gets a fresh copy of the task's starter package with the config's skills installed in
.claude/skills/. Claude runs with project settings only (no user settings, plugins or MCP).
Workspaces live under WORK_ROOT, outside the home directory: CLAUDE.md discovery walks ancestor
directories, so a workspace under ~ would load ~/.claude/CLAUDE.md (observed in a smoke run).
Any tool call touching a path outside the workspace is recorded as `outside_access`.
Outputs: evals/results/<stamp>/<task>/<config>/<n>/
  transcript.jsonl  stream-json agent transcript
  score.json        score.py output plus agent cost/turns/skill usage
  final/            the agent's Sources/ and Tests/ as scored
"""
import argparse
import concurrent.futures
import datetime
import json
import pathlib
import re
import shutil
import subprocess
import sys
import threading

EVALS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(EVALS))
import score  # noqa: E402

ALLOWED_TOOLS = ",".join([
    "Read", "Write", "Edit", "Glob", "Grep", "Skill",
    "Bash(swift build:*)", "Bash(swift test:*)", "Bash(swift package:*)",
    "Bash(xcodebuild:*)", "Bash(xcrun simctl list:*)", "Bash(ls:*)",
])
AGENT_TIMEOUT_S = 1500
SCORE_LOCK = threading.Lock()  # one simulator build/test at a time
WORK_ROOT = pathlib.Path("/private/tmp/ios-harness-evals")


def fetch_sources() -> pathlib.Path:
    """Clone each pinned upstream skill repo into evals/.sources/<name> at its recorded commit."""
    root = EVALS / ".sources"
    for name, spec in json.loads((EVALS / "sources.json").read_text()).items():
        dest = root / name
        if not dest.exists():
            subprocess.run(["git", "clone", "-q", spec["repo"], str(dest)], check=True)
        subprocess.run(["git", "-C", str(dest), "checkout", "-q", spec["commit"]], check=True)
    return root


def prepare_workspace(task_dir: pathlib.Path, config: dict, sources: pathlib.Path,
                      workspace: pathlib.Path) -> pathlib.Path:
    shutil.copytree(task_dir / "starter", workspace)
    for name, rel in config["skills"].items():
        shutil.copytree(sources / rel, workspace / ".claude" / "skills" / name)
    return workspace


def run_agent(prompt: str, workspace: pathlib.Path, model: str, transcript: pathlib.Path) -> dict:
    cmd = ["claude", "-p", prompt, "--model", model, "--output-format", "stream-json", "--verbose",
           "--setting-sources", "project", "--strict-mcp-config", "--no-session-persistence",
           "--no-chrome", "--allowedTools", ALLOWED_TOOLS]
    try:
        proc = subprocess.run(cmd, cwd=workspace, capture_output=True, text=True, timeout=AGENT_TIMEOUT_S)
        transcript.write_text(proc.stdout)
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        transcript.write_text(exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or ""))
        timed_out = True
    return summarize_transcript(transcript.read_text(), timed_out, workspace)


def tool_uses(text: str) -> tuple[list[dict], dict]:
    """All tool_use blocks in a stream-json transcript, plus the final result event."""
    uses: list[dict] = []
    result: dict = {}
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "result":
            result = event
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        uses += [b for b in message.get("content") or [] if isinstance(b, dict) and b.get("type") == "tool_use"]
    return uses, result


def outside_paths(tool_input: dict, workspace: pathlib.Path) -> list[str]:
    allowed = (str(workspace), str(workspace.resolve()), "/Applications/Xcode.app", "/dev/null")
    found = re.findall(r"(?:~|/(?:Users|private|tmp|var|etc|opt))[^\s'\"`;|&)]*", json.dumps(tool_input))
    return [p for p in found if not p.startswith(allowed)]


def summarize_transcript(text: str, timed_out: bool, workspace: pathlib.Path) -> dict:
    skills_used: set[str] = set()
    outside: set[str] = set()
    uses, result = tool_uses(text)
    for use in uses:
        tool_input = use.get("input") or {}
        if use.get("name") == "Skill":
            skills_used.add(str(tool_input.get("skill")))
        elif "/.claude/skills/" in str(tool_input.get("file_path", "")):
            skills_used.add(str(tool_input["file_path"]).split("/.claude/skills/")[1].split("/")[0])
        outside.update(outside_paths(tool_input, workspace))
    return {"agent_timed_out": timed_out, "agent_cost_usd": result.get("total_cost_usd"),
            "agent_turns": result.get("num_turns"), "agent_is_error": result.get("is_error"),
            "skills_used": sorted(skills_used), "outside_access": sorted(outside)}


def run_one(task_dir: pathlib.Path, config_name: str, rep: int, args: argparse.Namespace,
            sources: pathlib.Path, out: pathlib.Path) -> dict:
    config = json.loads((EVALS / "configs" / f"{config_name}.json").read_text())
    run_dir = out / task_dir.name / config_name / str(rep)
    run_dir.mkdir(parents=True)
    workspace = prepare_workspace(task_dir, config, sources,
                                  WORK_ROOT / out.name / task_dir.name / config_name / str(rep))
    agent = run_agent((task_dir / "prompt.md").read_text(), workspace, args.model, run_dir / "transcript.jsonl")
    for part in ("Sources", "Tests"):
        shutil.copytree(workspace / part, run_dir / "final" / part, dirs_exist_ok=True)
    with SCORE_LOCK:
        result = {"task": task_dir.name, "config": config_name, "rep": rep, **agent,
                  **score.score(task_dir, workspace)}
    (run_dir / "score.json").write_text(json.dumps(result, indent=2))
    print(f"{task_dir.name}/{config_name}/{rep}: hidden {result['hidden_passed']}/{result['hidden_total']} "
          f"lint {result['lint_violations']} warn {result['source_warnings']} cc {result['max_complexity']}",
          flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--configs", default="none,upstream")
    parser.add_argument("--tasks", default="")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--model", default="claude-opus-5-5")
    parser.add_argument("--parallel", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true", help="prepare workspaces only")
    args = parser.parse_args()

    tasks = sorted(p.parent for p in (EVALS / "tasks").glob("*/task.json")
                   if not args.tasks or p.parent.name in args.tasks.split(","))
    sources = fetch_sources()
    out = EVALS / "results" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    jobs = [(t, c, r) for t in tasks for c in args.configs.split(",") for r in range(args.repeats)]
    if args.dry_run:
        for t, c, r in jobs:
            config = json.loads((EVALS / "configs" / f"{c}.json").read_text())
            prepare_workspace(t, config, sources, WORK_ROOT / out.name / t.name / c / str(r))
        print(f"prepared {len(jobs)} workspaces in {WORK_ROOT / out.name}")
        return
    with concurrent.futures.ThreadPoolExecutor(args.parallel) as pool:
        results = list(pool.map(lambda job: run_one(*job, args, sources, out), jobs))
    (out / "results.json").write_text(json.dumps(results, indent=2))
    print(f"wrote {out / 'results.json'}")


if __name__ == "__main__":
    main()
