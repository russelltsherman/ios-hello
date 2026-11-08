After login our backend returns a session token. Implement token persistence in the `Auth` module of this Swift package (iOS 26).

Other code depends on these exact names:
- `struct TokenStore`, created with `TokenStore(service: String)` (the service name namespaces the stored token).
  - `func save(_ token: String) throws` — stores the token, replacing any existing one.
  - `func load() throws -> String?` — returns the stored token, or nil if none.
  - `func clear() throws` — removes the token; clearing when nothing is stored is not an error.

The token must survive app relaunches and must be stored securely on the device.

Add tests for your implementation.
