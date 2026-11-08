"""Extract ```swift blocks from skill markdown and typecheck each standalone.

Usage: python3 -I snippet_check.py <skill_dir> <out_dir> [--main-actor]
--main-actor typechecks with -default-isolation MainActor, matching the template's UI modules.
Each block is prefixed with Foundation/SwiftUI/Observation imports and typechecked for the
iOS 26 simulator in Swift 6 mode. Results: ok / warn / error (errors are often just fragments).
"""
import json
import pathlib
import re
import subprocess
import sys

BLOCK = re.compile(r"```swift\n(.*?)```", re.S)
PRELUDE = "import Foundation\nimport SwiftUI\nimport Observation\nimport Testing\n"
WRONG_MARK = re.compile(r"❌|// ?(bad|wrong|avoid|don't|before)\b", re.I)


def xcrun(*args: str) -> str:
    return subprocess.run(
        ["xcrun", *args], capture_output=True, text=True, check=True,
    ).stdout.strip()


def compiler_flags(main_actor: bool = False) -> list[str]:
    sdk = xcrun("--sdk", "iphonesimulator", "--show-sdk-path")
    platform_dev = xcrun("--sdk", "iphonesimulator", "--show-sdk-platform-path") + "/Developer"
    toolchain = pathlib.Path(xcrun("--find", "swiftc")).parent.parent
    return [
        "-target", "arm64-apple-ios26.0-simulator", "-sdk", sdk,
        "-F", f"{platform_dev}/Library/Frameworks", "-I", f"{platform_dev}/usr/lib",
        "-plugin-path", str(toolchain / "lib/swift/host/plugins/testing"),
        *(["-default-isolation", "MainActor", "-enable-upcoming-feature", "NonisolatedNonsendingByDefault"]
          if main_actor else []),
    ]


def check(code: str, path: pathlib.Path, flags: list[str]) -> tuple[str, str]:
    path.write_text(PRELUDE + code)
    proc = subprocess.run(
        ["xcrun", "swiftc", "-typecheck", "-swift-version", "6", "-parse-as-library",
         *flags, str(path)],
        capture_output=True, text=True, timeout=120,
    )
    out = proc.stderr
    if proc.returncode != 0:
        return "error", out
    return ("warn" if "warning:" in out else "ok"), out


def main() -> None:
    skill_dir, out_dir = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    flags = compiler_flags(main_actor="--main-actor" in sys.argv[3:])
    results = []
    for md in sorted(skill_dir.rglob("*.md")):
        for i, m in enumerate(BLOCK.finditer(md.read_text())):
            code = m.group(1)
            status, log = check(code, out_dir / f"{md.stem}_{i}.swift", flags)
            warnings = sorted(set(re.findall(r"warning: (.*)", log)))
            errors = sorted(set(re.findall(r"error: (.*)", log)))
            results.append({
                "file": str(md.relative_to(skill_dir)), "block": i, "status": status,
                "marked_negative": bool(WRONG_MARK.search(code)), "warnings": warnings,
                "errors": errors,
            })
    (out_dir / "results.json").write_text(json.dumps(results, indent=2))
    counts = {s: sum(r["status"] == s for r in results) for s in ("ok", "warn", "error")}
    print(skill_dir.name, len(results), counts)


if __name__ == "__main__":
    main()
