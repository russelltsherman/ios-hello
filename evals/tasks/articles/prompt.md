Add an article list feature to the `Articles` module of this Swift package (iOS 26, SwiftUI).

Other code depends on these exact names:
- `struct Article: Identifiable, Equatable, Sendable { let id: Int; let title: String }`
- `protocol ArticleClient: Sendable { func fetchArticles() async throws -> [Article] }`
- `enum LoadState: Equatable { case idle, loading, loaded([Article]), failed(String) }`
- `ArticleListModel`, created with `ArticleListModel(client:)`, exposing a readable `state: LoadState` (initially `.idle`) and `func load() async`, which sets `.loading`, then `.loaded` or `.failed` with a user-presentable message.
- `ArticleListView`, created with `ArticleListView(model:)`: loads when it appears, shows a progress indicator while loading, the titles when loaded, and an error message with a Retry button on failure.

Add tests for your implementation.
