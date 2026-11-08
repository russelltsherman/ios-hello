Implement app configuration loading in the `AppConfig` module of this Swift package (iOS 26).

The configuration arrives as JSON, for example:
`{ "apiBaseURL": "https://api.example.com", "timeoutSeconds": 30, "features": ["search", "offline"] }`

Other code depends on these exact names:
- `struct AppConfiguration: Equatable { let apiBaseURL: URL; let timeoutSeconds: Int; let features: Set<String> }`
- A `ConfigLoader` type with `static func load(from data: Data) throws -> AppConfiguration`.

Validation rules:
- `apiBaseURL` and `timeoutSeconds` are required; `features` is optional (defaults to empty).
- `apiBaseURL` must be an absolute `https` URL with a host.
- `timeoutSeconds` must be within 1...120.
- Invalid input of any kind must throw an error that tells callers what was wrong; never crash.

Add tests for your implementation.
