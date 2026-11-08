// swift-tools-version: 6.2
import PackageDescription

let settings: [SwiftSetting] = [
    .defaultIsolation(MainActor.self),
    .enableUpcomingFeature("NonisolatedNonsendingByDefault"),
    .enableUpcomingFeature("InferIsolatedConformances"),
]

let package = Package(
    name: "Greeting",
    platforms: [.macOS(.v26)],
    products: [.library(name: "Greeting", targets: ["Greeting"])],
    targets: [
        .target(name: "Greeting", swiftSettings: settings),
        .testTarget(name: "GreetingTests", dependencies: ["Greeting"], swiftSettings: settings),
    ]
)
