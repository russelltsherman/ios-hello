import Foundation
import Testing
@testable import Pricing

@Suite struct HiddenTests {
    let calc = PriceCalculator()

    func order(_ price: Decimal, _ qty: Int, member: Bool = false, coupon: String? = nil,
               region: Region = .other) -> Order {
        Order(unitPrice: price, quantity: qty, isMember: member, coupon: coupon, region: region)
    }

    @Test func zeroQuantityIsFree() { #expect(calc.total(for: order(10, 0)) == 0) }
    @Test func smallOrderPaysShipping() { #expect(calc.total(for: order(10, 1)) == Decimal(string: "14.99")) }
    @Test func freeShippingAtFifty() { #expect(calc.total(for: order(25, 2)) == 50) }
    @Test func tenItemsGetFivePercent() { #expect(calc.total(for: order(10, 10)) == 95) }
    @Test func fiftyItemsGetTenPercent() { #expect(calc.total(for: order(1, 50)) == Decimal(string: "49.99")) }
    @Test func hundredItemsGetFifteenPercent() { #expect(calc.total(for: order(1, 100)) == 85) }
    @Test func memberStacksMultiplicatively() { #expect(calc.total(for: order(10, 10, member: true)) == Decimal(string: "90.25")) }
    @Test func save10CaseInsensitive() { #expect(calc.total(for: order(100, 1, coupon: "save10")) == 90) }
    @Test func flat5NeverNegative() { #expect(calc.total(for: order(3, 1, coupon: "FLAT5")) == Decimal(string: "4.99")) }
    @Test func unknownCouponIgnored() { #expect(calc.total(for: order(100, 1, coupon: "BOGUS")) == 100) }
    @Test func usTaxExcludesShipping() { #expect(calc.total(for: order(10, 1, region: .us)) == Decimal(string: "15.69")) }
    @Test func euTaxOnDiscounted() { #expect(calc.total(for: order(100, 1, coupon: "SAVE10", region: .eu)) == 108) }
    @Test func roundsHalfUp() { #expect(calc.total(for: order(Decimal(string: "0.125")!, 1)) == Decimal(string: "5.12")) }
}
