import Foundation

/// Builds the greeting shown by `GreetingView`.
public enum Greeter {
    /// "Hello, World!" when `name` is nil or blank; otherwise "Hello, <trimmed name>!".
    public static func message(for name: String?) -> String {
        let trimmed = name?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        return "Hello, \(trimmed.isEmpty ? "World" : trimmed)!"
    }
}
