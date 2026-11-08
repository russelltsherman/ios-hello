Add a settings feature to the `Settings` module of this Swift package (iOS 26, SwiftUI).

Other code depends on these exact names:
- `struct SettingsSnapshot: Equatable, Sendable { var username: String; var notificationsEnabled: Bool }`
- `protocol SettingsStore { func load() -> SettingsSnapshot?; func save(_ snapshot: SettingsSnapshot) }`
- `SettingsModel`, created with `SettingsModel(store:)`, exposing readable `username` and `notificationsEnabled`.
  - Initial values come from `store.load()`; if nil, use `""` and `true`.
  - `toggleNotifications()` flips the flag and saves.
  - `rename(to:)` trims whitespace/newlines; empty results are ignored; otherwise updates and saves.
- `SettingsView`, created with `SettingsView(model:)`, lets the user edit the name and toggle notifications, and updates when the model changes.

Add tests for your implementation.
