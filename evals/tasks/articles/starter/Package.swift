// swift-tools-version: 6.2
import PackageDescription

let settings: [SwiftSetting] = [
    .defaultIsolation(MainActor.self),
    .enableUpcomingFeature("NonisolatedNonsendingByDefault"),
    .enableUpcomingFeature("InferIsolatedConformances"),
]

let package = Package(
    name: "Articles",
    platforms: [.iOS(.v26)],
    products: [.library(name: "Articles", targets: ["Articles"])],
    targets: [
        .target(name: "Articles", swiftSettings: settings),
        .testTarget(name: "ArticlesTests", dependencies: ["Articles"], swiftSettings: settings),
    ]
)
