"""scripts/verify: passes a clean package; fails on lint, format, compiler warnings or failing tests.

Each case builds a throwaway repo (configs + scripts + one package under Packages/) and runs verify.
Slow (one simulator build per case).
"""
import pathlib
import shutil
import subprocess
import tempfile
import textwrap
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = textwrap.dedent("""\
    // swift-tools-version: 6.2
    import PackageDescription

    let package = Package(
        name: "Widget",
        platforms: [PLATFORM],
        products: [.library(name: "Widget", targets: ["Widget"])],
        targets: [
            .target(name: "Widget"),
            .testTarget(name: "WidgetTests", dependencies: ["Widget"]),
        ]
    )
    """)
GOOD_SOURCE = "public func double(_ value: Int) -> Int {\n    value * 2\n}\n"
GOOD_TEST = textwrap.dedent("""\
    import Testing
    @testable import Widget

    @Test func doubles() {
        #expect(double(2) == 4)
    }
    """)


def make_repo(tmp: pathlib.Path, source: str = GOOD_SOURCE, test: str = GOOD_TEST,
              platform: str = ".iOS(.v26)", location: str = "Packages/Widget") -> pathlib.Path:
    repo = tmp / "repo"
    for item in (".swiftlint.yml", ".swift-format", "scripts"):
        target = repo / item
        if (ROOT / item).is_dir():
            shutil.copytree(ROOT / item, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / item, target)
    # Reuse the already-resolved pinned SwiftLint instead of downloading it per test.
    (repo / "tools").mkdir()
    (repo / "tools/lint").symlink_to(ROOT / "tools/lint")
    package = repo / location
    (package / "Sources/Widget").mkdir(parents=True)
    (package / "Tests/WidgetTests").mkdir(parents=True)
    (package / "Package.swift").write_text(PACKAGE.replace("PLATFORM", platform))
    (package / "Sources/Widget/Widget.swift").write_text(source)
    (package / "Tests/WidgetTests/WidgetTests.swift").write_text(test)
    return repo


def verify(repo: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(repo / "scripts/verify"), *args], cwd=repo, capture_output=True, text=True,
                          timeout=1200)


class VerifyTests(unittest.TestCase):
    def run_case(self, *args: str, **files: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            return verify(make_repo(pathlib.Path(tmp), **files), *args)

    def test_clean_package_passes(self) -> None:
        result = self.run_case()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_lint_violation_fails_fast_mode(self) -> None:
        result = self.run_case("--lint-only", source="public func first(_ values: [Int]) -> Int {\n    values.first!\n}\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("force_unwrapping", result.stdout + result.stderr)

    def test_format_violation_fails(self) -> None:
        result = self.run_case("--lint-only", source="public func double(_ value: Int) -> Int {\n  value * 2\n}\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("swift-format", result.stdout + result.stderr)

    def test_compiler_warning_fails(self) -> None:
        source = "public func double(_ value: Int) -> Int {\n    let unused = 1\n    return value * 2\n}\n"
        result = self.run_case(source=source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unused", result.stdout + result.stderr)

    def test_failing_test_fails(self) -> None:
        result = self.run_case(test=GOOD_TEST.replace("== 4", "== 5"))
        self.assertNotEqual(result.returncode, 0)

    # macOS: the destination must follow the package's primary platform. Before this was handled, an
    # iOS-simulator destination ran zero tests on a macOS-only package and verify reported success.
    def test_macos_package_passes(self) -> None:
        result = self.run_case(platform=".macOS(.v26)")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("platform=macOS", result.stdout)

    def test_macos_failing_test_fails(self) -> None:
        result = self.run_case(platform=".macOS(.v26)", test=GOOD_TEST.replace("== 4", "== 5"))
        self.assertNotEqual(result.returncode, 0)

    def test_macos_compiler_warning_fails(self) -> None:
        source = "public func double(_ value: Int) -> Int {\n    let unused = 1\n    return value * 2\n}\n"
        result = self.run_case(platform=".macOS(.v26)", source=source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unused", result.stdout + result.stderr)

    def test_primary_platform_is_first_declared(self) -> None:
        result = self.run_case(platform=".macOS(.v26), .iOS(.v26)")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("platform=macOS", result.stdout)

    def test_packages_under_app_are_verified(self) -> None:
        result = self.run_case(location="App/Widget", platform=".macOS(.v26)",
                               test=GOOD_TEST.replace("== 4", "== 5"))
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
