// swift-tools-version: 6.2
import PackageDescription

let settings: [SwiftSetting] = [
    .defaultIsolation(MainActor.self),
    .enableUpcomingFeature("NonisolatedNonsendingByDefault"),
    .enableUpcomingFeature("InferIsolatedConformances"),
]

let package = Package(
    name: "AppConfig",
    platforms: [.iOS(.v26)],
    products: [.library(name: "AppConfig", targets: ["AppConfig"])],
    targets: [
        .target(name: "AppConfig", swiftSettings: settings),
        .testTarget(name: "AppConfigTests", dependencies: ["AppConfig"], swiftSettings: settings),
    ]
)
