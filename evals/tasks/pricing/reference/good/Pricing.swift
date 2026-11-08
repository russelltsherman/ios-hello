import Foundation

public enum Region: Sendable {
    case us, eu, other

    var taxRate: Decimal {
        switch self {
        case .us: Decimal(string: "0.07") ?? 0
        case .eu: Decimal(string: "0.2") ?? 0
        case .other: 0
        }
    }
}

public struct Order: Sendable {
    let unitPrice: Decimal
    let quantity: Int
    let isMember: Bool
    let coupon: String?
    let region: Region

    public init(unitPrice: Decimal, quantity: Int, isMember: Bool, coupon: String?, region: Region) {
        self.unitPrice = unitPrice
        self.quantity = quantity
        self.isMember = isMember
        self.coupon = coupon
        self.region = region
    }
}

public struct PriceCalculator: Sendable {
    private static let freeShippingThreshold: Decimal = 50
    private static let shippingFee = Decimal(string: "4.99") ?? 0
    private static let volumeTiers: [(minimum: Int, rate: Decimal)] = [
        (100, Decimal(string: "0.15") ?? 0),
        (50, Decimal(string: "0.10") ?? 0),
        (10, Decimal(string: "0.05") ?? 0),
    ]

    public init() {}

    public func total(for order: Order) -> Decimal {
        guard order.quantity > 0 else { return 0 }
        let discounted = discountedAmount(for: order)
        let shipping = discounted >= Self.freeShippingThreshold ? 0 : Self.shippingFee
        return rounded(discounted + discounted * order.region.taxRate + shipping)
    }

    private func discountedAmount(for order: Order) -> Decimal {
        var amount = order.unitPrice * Decimal(order.quantity)
        amount *= 1 - volumeRate(for: order.quantity)
        if order.isMember { amount *= Decimal(string: "0.95") ?? 1 }
        return applyCoupon(order.coupon, to: amount)
    }

    private func volumeRate(for quantity: Int) -> Decimal {
        Self.volumeTiers.first { quantity >= $0.minimum }?.rate ?? 0
    }

    private func applyCoupon(_ coupon: String?, to amount: Decimal) -> Decimal {
        switch coupon?.uppercased() {
        case "SAVE10": amount * (Decimal(string: "0.9") ?? 1)
        case "FLAT5": max(0, amount - 5)
        default: amount
        }
    }

    private func rounded(_ value: Decimal) -> Decimal {
        var input = value
        var output = Decimal()
        NSDecimalRound(&output, &input, 2, .plain)
        return output
    }
}
