---
name: architecture
description: This project's app architecture - an MV/MVVM hybrid with @Observable feature models only where logic exists, thin SwiftUI views, SPM feature and core modules, protocol-based dependency clients injected through initializers or the environment, and a router that owns navigation state. Use when adding a feature, screen, module, service, dependency or navigation flow, when deciding where code belongs, or when reviewing structure and testability.
---

# Architecture

## Principles

1. **Views render state and forward intent.** No networking, persistence, parsing or business rules in a `View`.
2. **A feature model exists only when there is logic.** A screen that just displays values passed to it uses plain
   properties and `@State`. A screen with loading, validation, rules or side effects gets one `@Observable` model.
3. **Dependencies are protocols with a live and a test implementation, injected from outside.** No singletons, and
   no `URLSession.shared` or `FileManager.default` reached from a model.
4. **Modules enforce boundaries at compile time.** If code shouldn't depend on something, put it in a module that
   can't import it.
5. **Unidirectional flow:** view → model method → state change → view update. Children communicate up through
   closures or the model, never by mutating a parent's internals.

Third-party architecture frameworks (TCA, etc.) are not used. Do not introduce them.

## Module layout (local Swift packages)

```
App/                      # app target: composition root only (wiring, App struct, scenes)
Packages/
  Core/                   # Models, DesignSystem, Networking, Persistence, Testing helpers
  Features/
    Catalog/              # one package or target per feature: views + feature models
    Settings/
```

Dependency direction: `App → Features → Core`. **Features never import other features.** Cross-feature navigation
goes through closures or a router supplied by `App`. Core modules never import SwiftUI unless they are UI modules
(DesignSystem). Every feature target has a matching test target.

Swift settings for every target: Swift 6 language mode, `.defaultIsolation(MainActor.self)` for app and feature
(UI) modules, nonisolated default for Core service modules. Concurrency details are in `swift-concurrency`.

## Dependency clients

A client is a small protocol named for the capability, plus a live implementation in Core and test doubles in the
test target or a Core testing module.

```swift
import Foundation

struct Article: Identifiable, Equatable, Sendable {
    let id: Int
    let title: String
}

protocol ArticleClient: Sendable {
    func fetchArticles() async throws -> [Article]
}

struct LiveArticleClient: ArticleClient {
    let baseURL: URL
    let session: URLSession

    func fetchArticles() async throws -> [Article] {
        let (data, _) = try await session.data(from: baseURL.appending(path: "articles"))
        return try JSONDecoder().decode([ArticleDTO].self, from: data).map(\.article)
    }
}

private struct ArticleDTO: Decodable {
    let id: Int
    let title: String

    var article: Article { Article(id: id, title: title) }
}
```

Inject through the model's initializer. Construct live clients only in `App` (the composition root).

## Feature model

```swift
import Observation

struct Article: Identifiable, Equatable, Sendable {
    let id: Int
    let title: String
}

protocol ArticleClient: Sendable {
    func fetchArticles() async throws -> [Article]
}

enum LoadState: Equatable {
    case idle, loading, loaded([Article]), failed(String)
}

@MainActor
@Observable
final class ArticleListModel {
    private(set) var state: LoadState = .idle
    @ObservationIgnored private let client: any ArticleClient

    init(client: any ArticleClient) {
        self.client = client
    }

    func load() async {
        state = .loading
        do {
            state = .loaded(try await client.fetchArticles())
        } catch {
            state = .failed("Couldn't load articles. Try again.")
        }
    }
}
```

Rules:
- Model state is `private(set)`. Mutations go through intention-named methods (`load()`, `rename(to:)`), which
  are the unit-test surface.
- Mark dependencies `@ObservationIgnored`; they are not view state.
- Represent screen state as an enum when the states are mutually exclusive.
- A model never imports or references SwiftUI views. It may use `Observation` and Foundation.
- `@MainActor` is written explicitly above for clarity. Under `defaultIsolation(MainActor.self)` it is implied.

## Views

- Own a model with `@State private var model = Model(...)` only at the place that creates it. Pass it down as a
  plain `let` (read-only) or as `@Bindable` (needs bindings).
- Never use `ObservableObject`, `@Published`, `@StateObject`, `@ObservedObject` or `@EnvironmentObject` in new code.
- Use `@Environment` for app-wide dependencies that many views need, via an `@Entry` with a stable value-type default
  (never `@Entry var x = SomeClass()`, which re-allocates on every fallback read).
- Extract subviews once a `body` has more than a few distinct sections. Extract them as `View` structs, not
  computed properties returning `some View`, when they have their own inputs.

## Navigation

The router owns navigation state, so deep links and tests can drive it without UI:

```swift
import Observation
import SwiftUI

struct Product: Identifiable, Hashable, Sendable {
    let id: Int
    let name: String
}

@MainActor
@Observable
final class CatalogRouter {
    var path: [Product] = []

    func show(_ product: Product) { path.append(product) }
    func popToRoot() { path.removeAll() }
}

struct CatalogView: View {
    let products: [Product]
    @Bindable var router: CatalogRouter

    var body: some View {
        NavigationStack(path: $router.path) {
            List(products) { NavigationLink($0.name, value: $0) }
                .navigationDestination(for: Product.self) { Text($0.name) }
        }
    }
}
```

Use `NavigationStack(path:)` with value-based `NavigationLink(_:value:)` and `.navigationDestination(for:)`. Never
`NavigationView` or `NavigationLink(destination:)` / `isActive:`.

## Testing seams

| Layer | Test with |
|---|---|
| Feature model | Swift Testing + fake clients; assert state transitions after awaiting methods |
| Client (live) | Integration tests behind a tag, or `URLProtocol` stubs; never hit production in unit tests |
| Router | Plain unit tests on `path` |
| Views | Previews with fake data; UI tests (XCTest) only for critical flows |

## Where does this code go?

| Code | Location |
|---|---|
| Domain types shared by several features | `Core/Models` |
| HTTP, persistence, Keychain | `Core/<Capability>` behind a client protocol |
| Screen logic | Feature model in the feature module |
| Layout, styling, formatting for display | View, or `Core/DesignSystem` if reused |
| Wiring live clients, app lifecycle, scenes | `App` |
