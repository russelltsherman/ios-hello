// swift-tools-version: 6.2
import PackageDescription

let settings: [SwiftSetting] = [
    .defaultIsolation(MainActor.self),
    .enableUpcomingFeature("NonisolatedNonsendingByDefault"),
    .enableUpcomingFeature("InferIsolatedConformances"),
]

let package = Package(
    name: "Settings",
    platforms: [.iOS(.v26)],
    products: [.library(name: "Settings", targets: ["Settings"])],
    targets: [
        .target(name: "Settings", swiftSettings: settings),
        .testTarget(name: "SettingsTests", dependencies: ["Settings"], swiftSettings: settings),
    ]
)
