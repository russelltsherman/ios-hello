import Observation
import SwiftUI

public struct Product: Identifiable, Hashable, Sendable {
    public let id: Int
    public let name: String

    public init(id: Int, name: String) {
        self.id = id
        self.name = name
    }
}

@Observable
public final class CatalogRouter {
    public var path: [Product] = []

    public init() {}

    public func show(_ product: Product) {
        path.append(product)
    }

    public func popToRoot() {
        path.removeAll()
    }
}

public struct CatalogView: View {
    let products: [Product]
    @Bindable var router: CatalogRouter

    public init(products: [Product], router: CatalogRouter) {
        self.products = products
        self.router = router
    }

    public var body: some View {
        NavigationStack(path: $router.path) {
            List(products) { product in
                NavigationLink(product.name, value: product)
            }
            .navigationTitle("Catalog")
            .navigationDestination(for: Product.self) { ProductDetailView(product: $0) }
        }
    }
}

public struct ProductDetailView: View {
    let product: Product

    public init(product: Product) {
        self.product = product
    }

    public var body: some View {
        Text(product.name)
            .font(.largeTitle)
            .navigationTitle(product.name)
    }
}
