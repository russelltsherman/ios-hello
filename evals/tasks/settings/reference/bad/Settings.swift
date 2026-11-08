import Combine
import SwiftUI

public struct SettingsSnapshot: Equatable, Sendable {
    public var username: String
    public var notificationsEnabled: Bool

    public init(username: String, notificationsEnabled: Bool) {
        self.username = username
        self.notificationsEnabled = notificationsEnabled
    }
}

public protocol SettingsStore {
    func load() -> SettingsSnapshot?
    func save(_ snapshot: SettingsSnapshot)
}

public final class SettingsModel: ObservableObject {
    @Published public private(set) var username: String
    @Published public var notificationsEnabled: Bool {
        didSet { persist() }
    }
    private let store: any SettingsStore

    public init(store: any SettingsStore) {
        self.store = store
        let snapshot = store.load() ?? SettingsSnapshot(username: "", notificationsEnabled: true)
        username = snapshot.username
        notificationsEnabled = snapshot.notificationsEnabled
    }

    public func toggleNotifications() {
        notificationsEnabled.toggle()
    }

    public func rename(to newName: String) {
        let trimmed = newName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        username = trimmed
        persist()
    }

    private func persist() {
        store.save(SettingsSnapshot(username: username, notificationsEnabled: notificationsEnabled))
    }
}

public struct SettingsView: View {
    @ObservedObject var model: SettingsModel
    @State private var draftName = ""

    public init(model: SettingsModel) {
        self.model = model
    }

    public var body: some View {
        Form {
            TextField("Username", text: $draftName)
                .onSubmit { model.rename(to: draftName) }
            Toggle("Notifications", isOn: $model.notificationsEnabled)
        }
        .onAppear { draftName = model.username }
    }
}
