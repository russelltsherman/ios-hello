// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "HelloMac",
    platforms: [.macOS(.v26)],
    dependencies: [
        .package(path: "../../Packages/Features/Greeting")
    ],
    targets: [
        .executableTarget(
            name: "HelloMac",
            dependencies: [.product(name: "Greeting", package: "Greeting")],
            swiftSettings: [
                .defaultIsolation(MainActor.self),
                .enableUpcomingFeature("NonisolatedNonsendingByDefault"),
                .enableUpcomingFeature("InferIsolatedConformances"),
            ]
        )
    ]
)
