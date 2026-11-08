// swift-tools-version: 6.2
import PackageDescription

let settings: [SwiftSetting] = [
    .defaultIsolation(MainActor.self),
    .enableUpcomingFeature("NonisolatedNonsendingByDefault"),
    .enableUpcomingFeature("InferIsolatedConformances"),
]

let package = Package(
    name: "Catalog",
    platforms: [.iOS(.v26)],
    products: [.library(name: "Catalog", targets: ["Catalog"])],
    targets: [
        .target(name: "Catalog", swiftSettings: settings),
        .testTarget(name: "CatalogTests", dependencies: ["Catalog"], swiftSettings: settings),
    ]
)
