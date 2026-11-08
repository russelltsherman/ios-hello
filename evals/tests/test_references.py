"""Validate each eval task with its reference solutions.

good/ must build without warnings, pass every hidden test, have zero lint violations, no forbidden
patterns and no missing required patterns. bad/ (optional) must trip every key in the task's
`bad_expectations` (dotted paths into the score, e.g. "lint_by_rule.force_unwrapping").
Slow: one simulator build+test per reference. Run: python3 -I -m unittest evals.tests.test_references
"""
import json
import pathlib
import shutil
import sys
import tempfile
import unittest

EVALS = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EVALS))
import score  # noqa: E402

TASKS = sorted(p.parent for p in (EVALS / "tasks").glob("*/task.json"))


def score_reference(task_dir: pathlib.Path, variant: str) -> dict:
    task = json.loads((task_dir / "task.json").read_text())
    with tempfile.TemporaryDirectory() as tmp:
        workspace = pathlib.Path(tmp) / "ws"
        shutil.copytree(task_dir / "starter", workspace)
        for source in (task_dir / "reference" / variant).glob("*.swift"):
            shutil.copy(source, workspace / "Sources" / task["module"] / source.name)
        return score.score(task_dir, workspace)


def lookup(result: dict, dotted: str) -> object:
    head, _, tail = dotted.partition(".")
    value = result[head]
    return (tail in value) if isinstance(value, list) else value.get(tail, 0)


class ReferenceTests(unittest.TestCase):
    def test_good_references_score_clean(self) -> None:
        for task_dir in TASKS:
            with self.subTest(task=task_dir.name):
                result = score_reference(task_dir, "good")
                self.assertTrue(result["build_ok"], result)
                self.assertEqual(result["source_warnings"], 0, result["warning_lines"])
                self.assertEqual(result["hidden_passed"], result["hidden_total"], result)
                self.assertEqual(result["lint_violations"], 0, result["lint_by_rule"])
                self.assertEqual(sum(result["forbidden"].values()), 0, result["forbidden"])
                self.assertEqual(result["required_missing"], [])

    def test_bad_references_trip_expectations(self) -> None:
        for task_dir in TASKS:
            expectations = json.loads((task_dir / "task.json").read_text()).get("bad_expectations", [])
            if not (task_dir / "reference/bad").exists():
                continue
            with self.subTest(task=task_dir.name):
                self.assertTrue(expectations, "bad reference without bad_expectations")
                result = score_reference(task_dir, "bad")
                for key in expectations:
                    self.assertTrue(lookup(result, key), f"{key} not tripped: {result}")


if __name__ == "__main__":
    unittest.main()
