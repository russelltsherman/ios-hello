"""Fast unit tests for score.py log parsing (no builds)."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import score  # noqa: E402


class HiddenResultsTests(unittest.TestCase):
    def test_parameterized_and_interleaved_output(self) -> None:
        log = (
            "◇ Test featuresDefaultToEmpty() started.\n"
            "✔ Test timeoutOutOfRangeThrows(timeout:) with 3 test cases passed after 0.018 seconds.\n"
            "✔ Test run with 6 tests in 1 suite passed after 0.023 seconds.\n"
        )
        self.assertEqual(score.hidden_results(log), (6, 0))

    def test_failures_counted_once_per_test(self) -> None:
        log = (
            "✘ Test roundTrip() recorded an issue at HiddenTests.swift:12:6: Caught error\n"
            "✘ Test roundTrip() failed after 0.003 seconds with 1 issue.\n"
            "✘ Test run with 4 tests in 1 suite failed after 0.05 seconds with 1 issue.\n"
        )
        self.assertEqual(score.hidden_results(log), (3, 1))

    def test_no_run_means_nothing_compiled(self) -> None:
        self.assertEqual(score.hidden_results("error: cannot find 'Order' in scope\n"), (0, 0))


if __name__ == "__main__":
    unittest.main()
