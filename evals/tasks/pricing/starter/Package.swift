// swift-tools-version: 6.2
import PackageDescription

let settings: [SwiftSetting] = [
    .defaultIsolation(MainActor.self),
    .enableUpcomingFeature("NonisolatedNonsendingByDefault"),
    .enableUpcomingFeature("InferIsolatedConformances"),
]

let package = Package(
    name: "Pricing",
    platforms: [.iOS(.v26)],
    products: [.library(name: "Pricing", targets: ["Pricing"])],
    targets: [
        .target(name: "Pricing", swiftSettings: settings),
        .testTarget(name: "PricingTests", dependencies: ["Pricing"], swiftSettings: settings),
    ]
)
