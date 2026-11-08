import Foundation

public enum Region { case us, eu, other }

public struct Order {
    var unitPrice: Decimal; var quantity: Int; var isMember: Bool; var coupon: String?; var region: Region
    public init(unitPrice: Decimal, quantity: Int, isMember: Bool, coupon: String?, region: Region) {
        self.unitPrice = unitPrice; self.quantity = quantity; self.isMember = isMember
        self.coupon = coupon; self.region = region
    }
}

public struct PriceCalculator {
    public init() {}
    public func total(for order: Order) -> Decimal {
        if order.quantity <= 0 { return 0 }
        var amount = order.unitPrice * Decimal(order.quantity)
        if order.quantity >= 100 {
            amount = amount * Decimal(string: "0.85")!
        } else if order.quantity >= 50 {
            amount = amount * Decimal(string: "0.90")!
        } else if order.quantity >= 10 {
            amount = amount * Decimal(string: "0.95")!
        }
        if order.isMember { amount = amount * Decimal(string: "0.95")! }
        if order.coupon != nil {
            if order.coupon!.uppercased() == "SAVE10" {
                amount = amount * Decimal(string: "0.9")!
            } else if order.coupon!.uppercased() == "FLAT5" {
                amount = amount - 5
                if amount < 0 { amount = 0 }
            }
        }
        var tax: Decimal = 0
        if order.region == .us { tax = amount * Decimal(string: "0.07")! } else if order.region == .eu { tax = amount * Decimal(string: "0.2")! }
        var shipping: Decimal = 0
        if amount < 50 { shipping = Decimal(string: "4.99")! }
        var total = amount + tax + shipping
        var result = Decimal()
        NSDecimalRound(&result, &total, 2, .plain)
        return result
    }
}
