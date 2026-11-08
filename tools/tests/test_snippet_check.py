"""Known-answer test for snippet_check.py: ok / warn / error / Swift Testing macro block."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).parent


class SnippetCheckTests(unittest.TestCase):
    def test_classifies_known_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as out:
            subprocess.run(
                [sys.executable, "-I", str(HERE.parent / "snippet_check.py"),
                 str(HERE / "fixtures"), out],
                check=True, capture_output=True,
            )
            results = json.loads((pathlib.Path(out) / "results.json").read_text())
        self.assertEqual([r["status"] for r in results], ["ok", "warn", "error", "ok"])


if __name__ == "__main__":
    unittest.main()
