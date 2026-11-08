"""Transcript parsing: skill usage, outside-workspace access, and non-dict message events."""
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import run_eval  # noqa: E402

WS = pathlib.Path("/private/tmp/ios-harness-evals/x/pricing/none/0")


def event(*blocks: dict) -> str:
    return json.dumps({"type": "assistant", "message": {"content": list(blocks)}})


def tool(name: str, **tool_input: str) -> dict:
    return {"type": "tool_use", "name": name, "input": tool_input}


class TranscriptTests(unittest.TestCase):
    def test_flags_reads_outside_workspace(self) -> None:
        text = "\n".join([
            json.dumps({"type": "system", "subtype": "permission_denied", "message": "blocked"}),
            event(tool("Bash", command=f"cat {WS}/Package.swift; cat ~/.agents/AGENTS.md")),
            event(tool("Read", file_path="/Users/someone/.agents/USER.md")),
            event(tool("Read", file_path=f"{WS}/Sources/Pricing/Pricing.swift")),
            json.dumps({"type": "result", "total_cost_usd": 0.1, "num_turns": 3, "is_error": False}),
        ])
        summary = run_eval.summarize_transcript(text, False, WS)
        self.assertEqual(summary["outside_access"], ["/Users/someone/.agents/USER.md", "~/.agents/AGENTS.md"])
        self.assertEqual(summary["agent_turns"], 3)

    def test_records_skill_usage(self) -> None:
        text = "\n".join([
            event(tool("Skill", skill="swiftui-pro")),
            event(tool("Read", file_path=f"{WS}/.claude/skills/swift-concurrency/references/tasks.md")),
        ])
        summary = run_eval.summarize_transcript(text, False, WS)
        self.assertEqual(summary["skills_used"], ["swift-concurrency", "swiftui-pro"])
        self.assertEqual(summary["outside_access"], [])

    def test_xcode_paths_are_not_outside_access(self) -> None:
        text = event(tool("Bash", command="xcrun --find swiftc  # /Applications/Xcode.app/Contents/Developer"))
        self.assertEqual(run_eval.summarize_transcript(text, False, WS)["outside_access"], [])


if __name__ == "__main__":
    unittest.main()
