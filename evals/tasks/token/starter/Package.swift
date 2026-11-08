// swift-tools-version: 6.2
import PackageDescription

let settings: [SwiftSetting] = [
    .defaultIsolation(MainActor.self),
    .enableUpcomingFeature("NonisolatedNonsendingByDefault"),
    .enableUpcomingFeature("InferIsolatedConformances"),
]

let package = Package(
    name: "Auth",
    platforms: [.iOS(.v26), .macOS(.v26)],
    products: [.library(name: "Auth", targets: ["Auth"])],
    targets: [
        .target(name: "Auth", swiftSettings: settings),
        .testTarget(name: "AuthTests", dependencies: ["Auth"], swiftSettings: settings),
    ]
)
