Implement order pricing in the `Pricing` module of this Swift package.

Public API (other code depends on these exact names):
- `enum Region { case us, eu, other }`
- `struct Order { init(unitPrice: Decimal, quantity: Int, isMember: Bool, coupon: String?, region: Region) }`
- `struct PriceCalculator { init(); func total(for order: Order) -> Decimal }`

Rules, applied in this order:
1. If quantity <= 0 the total is 0.
2. Subtotal = unitPrice × quantity.
3. Volume discount on the subtotal: quantity >= 100 → 15% off, >= 50 → 10% off, >= 10 → 5% off.
4. Members get a further 5% off the result of step 3.
5. Coupons (case-insensitive) apply to the result of step 4: "SAVE10" → 10% off; "FLAT5" → $5 off (never below 0). Unknown coupons are ignored.
6. Tax on the discounted amount: US 7%, EU 20%, other 0%.
7. Shipping: free if the discounted amount (before tax) is >= 50, otherwise 4.99. Shipping is not taxed.
8. Total = discounted amount + tax + shipping, rounded to 2 decimal places (half up).

Add tests for your implementation.
