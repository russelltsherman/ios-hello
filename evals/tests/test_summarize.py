"""summarize.py aggregates repeats per task/config."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import summarize  # noqa: E402


def result(config: str, passed: int, lint: int, forbidden: int, skills: list[str]) -> dict:
    return {"task": "settings", "config": config, "hidden_passed": passed, "hidden_total": 4,
            "build_ok": True, "source_warnings": 0, "lint_violations": lint, "max_complexity": 2,
            "forbidden": {"ObservableObject": forbidden}, "required_missing": [], "metrics": {},
            "lint_by_rule": {"force_unwrapping": lint} if lint else {}, "agent_cost_usd": 0.5,
            "skills_used": skills, "outside_access": []}


class SummarizeTests(unittest.TestCase):
    def test_means_over_repeats(self) -> None:
        results = [result("none", 4, 2, 1, []), result("none", 2, 0, 1, []),
                   result("upstream", 4, 0, 0, ["swiftui-pro"])]
        rows = summarize.table(results).splitlines()
        self.assertIn("| settings | none | 2 | 75% | 100% | 0.0 | 1.0 | 2.0 | 1.0 |", rows[2])
        self.assertIn("swiftui-pro×1", rows[3])

    def test_details_sum_patterns(self) -> None:
        text = summarize.details([result("none", 4, 2, 1, []), result("none", 4, 0, 2, [])])
        self.assertIn("forbidden: ObservableObject=3", text)
        self.assertIn("lint: force_unwrapping=2", text)


if __name__ == "__main__":
    unittest.main()
