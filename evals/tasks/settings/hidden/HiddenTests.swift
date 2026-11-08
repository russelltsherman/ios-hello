import Testing
@testable import Settings

final class HiddenFakeStore: SettingsStore {
    var stored: SettingsSnapshot?
    private(set) var saves: [SettingsSnapshot] = []
    init(_ stored: SettingsSnapshot? = nil) { self.stored = stored }
    func load() -> SettingsSnapshot? { stored }
    func save(_ snapshot: SettingsSnapshot) { saves.append(snapshot); stored = snapshot }
}

@Suite struct HiddenTests {
    @Test func defaultsWhenStoreEmpty() {
        let model = SettingsModel(store: HiddenFakeStore())
        #expect(model.username == "")
        #expect(model.notificationsEnabled == true)
    }

    @Test func loadsFromStore() {
        let model = SettingsModel(store: HiddenFakeStore(SettingsSnapshot(username: "ana", notificationsEnabled: false)))
        #expect(model.username == "ana")
        #expect(model.notificationsEnabled == false)
    }

    @Test func toggleSaves() {
        let store = HiddenFakeStore()
        let model = SettingsModel(store: store)
        model.toggleNotifications()
        #expect(model.notificationsEnabled == false)
        #expect(store.saves.last == SettingsSnapshot(username: "", notificationsEnabled: false))
    }

    @Test func renameTrimsAndSaves() {
        let store = HiddenFakeStore()
        let model = SettingsModel(store: store)
        model.rename(to: "  Bo \n")
        #expect(model.username == "Bo")
        #expect(store.saves.last?.username == "Bo")
    }

    @Test func emptyRenameIgnored() {
        let store = HiddenFakeStore(SettingsSnapshot(username: "ana", notificationsEnabled: true))
        let model = SettingsModel(store: store)
        model.rename(to: "   ")
        #expect(model.username == "ana")
        #expect(store.saves.isEmpty)
        _ = SettingsView(model: model)
    }
}
