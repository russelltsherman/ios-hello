import Foundation
import Testing
@testable import AppConfig

@Suite struct HiddenTests {
    func json(_ text: String) -> Data { Data(text.utf8) }

    @Test func parsesValidConfig() throws {
        let config = try ConfigLoader.load(from: json(
            #"{"apiBaseURL":"https://api.example.com","timeoutSeconds":30,"features":["search","offline"]}"#))
        #expect(config.apiBaseURL.host() == "api.example.com")
        #expect(config.timeoutSeconds == 30)
        #expect(config.features == ["search", "offline"])
    }

    @Test func featuresDefaultToEmpty() throws {
        let config = try ConfigLoader.load(from: json(#"{"apiBaseURL":"https://a.b","timeoutSeconds":5}"#))
        #expect(config.features.isEmpty)
    }

    @Test func malformedJSONThrows() {
        #expect(throws: (any Error).self) { try ConfigLoader.load(from: json("{not json")) }
    }

    @Test func missingRequiredKeyThrows() {
        #expect(throws: (any Error).self) { try ConfigLoader.load(from: json(#"{"timeoutSeconds":5}"#)) }
    }

    @Test func insecureURLThrows() {
        #expect(throws: (any Error).self) {
            try ConfigLoader.load(from: json(#"{"apiBaseURL":"http://a.b","timeoutSeconds":5}"#))
        }
    }

    @Test(arguments: [0, 121, -1])
    func timeoutOutOfRangeThrows(timeout: Int) {
        #expect(throws: (any Error).self) {
            try ConfigLoader.load(from: json(#"{"apiBaseURL":"https://a.b","timeoutSeconds":\#(timeout)}"#))
        }
    }
}
