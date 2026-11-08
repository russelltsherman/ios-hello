Build catalog browsing in the `Catalog` module of this Swift package (iOS 26, SwiftUI).

Other code depends on these exact names:
- `struct Product: Identifiable, Hashable, Sendable { let id: Int; let name: String }`
- `CatalogRouter`, created with `CatalogRouter()`, that owns navigation state:
  - `path: [Product]` (readable; empty means the catalog root is showing)
  - `func show(_ product: Product)` pushes the product's detail screen
  - `func popToRoot()` returns to the catalog
- `CatalogView`, created with `CatalogView(products:router:)`, shows a list of products; tapping one opens `ProductDetailView`. Navigation must stay in sync with the router so deep links can call `router.show(_:)`.
- `ProductDetailView`, created with `ProductDetailView(product:)`, shows the product name.

Add tests for your implementation.
