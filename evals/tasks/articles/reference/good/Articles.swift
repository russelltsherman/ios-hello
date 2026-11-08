import Observation
import SwiftUI

public struct Article: Identifiable, Equatable, Sendable {
    public let id: Int
    public let title: String

    public init(id: Int, title: String) {
        self.id = id
        self.title = title
    }
}

public protocol ArticleClient: Sendable {
    func fetchArticles() async throws -> [Article]
}

public enum LoadState: Equatable {
    case idle, loading, loaded([Article]), failed(String)
}

@Observable
public final class ArticleListModel {
    public private(set) var state: LoadState = .idle
    @ObservationIgnored private let client: any ArticleClient

    public init(client: any ArticleClient) {
        self.client = client
    }

    public func load() async {
        state = .loading
        do {
            state = .loaded(try await client.fetchArticles())
        } catch {
            state = .failed("Couldn't load articles. Check your connection and try again.")
        }
    }
}

public struct ArticleListView: View {
    let model: ArticleListModel

    public init(model: ArticleListModel) {
        self.model = model
    }

    public var body: some View {
        content
            .task { await model.load() }
    }

    @ViewBuilder private var content: some View {
        switch model.state {
        case .idle, .loading:
            ProgressView()
        case .loaded(let articles):
            List(articles) { Text($0.title) }
        case .failed(let message):
            ContentUnavailableView {
                Label("Unavailable", systemImage: "exclamationmark.triangle")
            } description: {
                Text(message)
            } actions: {
                Button("Retry") { Task { await model.load() } }
            }
        }
    }
}
