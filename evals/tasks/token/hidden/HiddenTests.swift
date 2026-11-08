import Foundation
import Testing
@testable import Auth

@Suite(.serialized) struct HiddenTests {
    let store = TokenStore(service: "eval.hidden.\(UUID().uuidString)")

    @Test func missingTokenIsNil() throws {
        #expect(try store.load() == nil)
    }

    @Test func roundTrip() throws {
        try store.save("abc123")
        #expect(try store.load() == "abc123")
        try store.clear()
    }

    @Test func saveReplaces() throws {
        try store.save("first")
        try store.save("second")
        #expect(try store.load() == "second")
        try store.clear()
    }

    @Test func clearRemovesAndIsIdempotent() throws {
        try store.save("gone")
        try store.clear()
        try store.clear()
        #expect(try store.load() == nil)
    }
}
