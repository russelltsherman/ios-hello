// swift-tools-version: 6.2
// Pins the SwiftLint binary used by hooks, CI and the eval scorer.
import PackageDescription

let package = Package(
    name: "HarnessLint",
    dependencies: [
        .package(url: "https://github.com/SimplyDanny/SwiftLintPlugins", exact: "0.65.1"),
    ],
    targets: []
)
