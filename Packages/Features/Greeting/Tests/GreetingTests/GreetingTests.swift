import Testing

@testable import Greeting

@Suite struct GreeterTests {
    @Test(arguments: [nil, "", "   ", "\n\t"] as [String?])
    func blankOrMissingNameGreetsTheWorld(name: String?) {
        #expect(Greeter.message(for: name) == "Hello, World!")
    }

    @Test(arguments: [
        ("Ada", "Hello, Ada!"),
        ("  Grace \n", "Hello, Grace!"),
        ("Tim Berners-Lee", "Hello, Tim Berners-Lee!"),
    ])
    func namedGreetingUsesTrimmedName(name: String, expected: String) {
        #expect(Greeter.message(for: name) == expected)
    }

    @Test func viewCanBeCreated() {
        _ = GreetingView()
    }
}
