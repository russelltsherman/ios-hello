"""Lint gate: the harness .swiftlint.yml must pass clean code and fail complex / force-unwrapping code."""
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SWIFTLINT = (ROOT / "tools/lint/.build/artifacts/swiftlintplugins/SwiftLintBinary"
             / "SwiftLintBinary.artifactbundle/macos/swiftlint")
FIXTURES = pathlib.Path(__file__).parent / "fixtures/lint"


def lint(fixture: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp) / fixture
        shutil.copytree(FIXTURES / fixture / "Sources", work / "Sources")
        shutil.copy(ROOT / ".swiftlint.yml", work / ".swiftlint.yml")
        return subprocess.run([str(SWIFTLINT), "lint", "--strict", "--quiet"],
                              cwd=work, capture_output=True, text=True)


@unittest.skipUnless(SWIFTLINT.exists(), "run `swift package resolve` in tools/lint first")
class LintGateTests(unittest.TestCase):
    def test_clean_code_passes(self) -> None:
        self.assertEqual(lint("good").returncode, 0)

    def test_swift_format_output_passes_lint(self) -> None:
        source = ROOT / "evals/tasks/pricing/reference/good/Pricing.swift"
        with tempfile.TemporaryDirectory() as tmp:
            work = pathlib.Path(tmp)
            (work / "Sources").mkdir()
            shutil.copy(source, work / "Sources/Pricing.swift")
            for config in (".swiftlint.yml", ".swift-format"):
                shutil.copy(ROOT / config, work / config)
            subprocess.run(["xcrun", "swift-format", "format", "-i", "--configuration", ".swift-format",
                            "Sources/Pricing.swift"], cwd=work, check=True)
            result = subprocess.run([str(SWIFTLINT), "lint", "--strict", "--quiet"],
                                    cwd=work, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_complex_force_unwrapping_code_fails(self) -> None:
        result = lint("bad")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("(cyclomatic_complexity)", result.stdout)
        self.assertIn("(force_unwrapping)", result.stdout)


if __name__ == "__main__":
    unittest.main()
