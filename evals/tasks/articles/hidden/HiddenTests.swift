import Testing
@testable import Articles

nonisolated struct HiddenStubClient: ArticleClient {
    struct Failure: Error {}
    let articles: [Article]?
    func fetchArticles() async throws -> [Article] {
        guard let articles else { throw Failure() }
        return articles
    }
}

@Suite struct HiddenTests {
    @Test func startsIdle() {
        #expect(ArticleListModel(client: HiddenStubClient(articles: [])).state == .idle)
    }

    @Test func loadsArticles() async {
        let articles = [Article(id: 1, title: "One"), Article(id: 2, title: "Two")]
        let model = ArticleListModel(client: HiddenStubClient(articles: articles))
        await model.load()
        #expect(model.state == .loaded(articles))
        _ = ArticleListView(model: model)
    }

    @Test func failureProducesMessage() async {
        let model = ArticleListModel(client: HiddenStubClient(articles: nil))
        await model.load()
        guard case .failed(let message) = model.state else {
            Issue.record("expected failed state, got \(model.state)")
            return
        }
        #expect(!message.isEmpty)
    }
}
