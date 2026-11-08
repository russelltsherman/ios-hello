import Foundation

public struct AppConfiguration: Equatable, Sendable {
    public let apiBaseURL: URL
    public let timeoutSeconds: Int
    public let features: Set<String>
}

public enum ConfigError: Error, Equatable {
    case malformed(String)
    case insecureURL(String)
    case timeoutOutOfRange(Int)
}

public enum ConfigLoader {
    private static let allowedTimeouts = 1...120

    private struct Payload: Decodable {
        let apiBaseURL: String
        let timeoutSeconds: Int
        let features: Set<String>?
    }

    public static func load(from data: Data) throws(ConfigError) -> AppConfiguration {
        let payload: Payload
        do {
            payload = try JSONDecoder().decode(Payload.self, from: data)
        } catch {
            throw .malformed(String(describing: error))
        }
        guard let url = URL(string: payload.apiBaseURL), url.scheme == "https", url.host() != nil else {
            throw .insecureURL(payload.apiBaseURL)
        }
        guard allowedTimeouts.contains(payload.timeoutSeconds) else {
            throw .timeoutOutOfRange(payload.timeoutSeconds)
        }
        return AppConfiguration(
            apiBaseURL: url, timeoutSeconds: payload.timeoutSeconds, features: payload.features ?? []
        )
    }
}
