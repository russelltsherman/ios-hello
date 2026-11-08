import AppKit
import Greeting
import SwiftUI

/// Composition root: wires the Greeting feature into a window. No logic lives here.
@main
struct HelloMacApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    var body: some Scene {
        WindowGroup("Hello, Mac") {
            GreetingView()
        }
        .windowResizability(.contentSize)
    }
}

/// A SwiftPM executable has no Info.plist, so macOS registers it as a background-only process:
/// its window opens behind other apps and it gets no Dock icon. Promote it to a regular app.
final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApplication.shared.setActivationPolicy(.regular)
        NSApplication.shared.activate()
    }
}
