import Testing
@testable import Catalog

@Suite struct HiddenTests {
    let phone = Product(id: 1, name: "Phone")
    let watch = Product(id: 2, name: "Watch")

    @Test func startsAtRoot() {
        #expect(CatalogRouter().path.isEmpty)
    }

    @Test func showPushes() {
        let router = CatalogRouter()
        router.show(phone)
        router.show(watch)
        #expect(router.path == [phone, watch])
        _ = CatalogView(products: [phone, watch], router: router)
        _ = ProductDetailView(product: phone)
    }

    @Test func popToRootClears() {
        let router = CatalogRouter()
        router.show(phone)
        router.popToRoot()
        #expect(router.path.isEmpty)
    }
}
