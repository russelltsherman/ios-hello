---
name: complexity-refactoring
description: Keep Swift functions under the harness complexity limits and refactor them when they exceed. Use when writing or changing Swift with branching business rules (pricing, validation, state machines, permissions, parsing), when SwiftLint reports cyclomatic_complexity, function_body_length, closure_body_length, nesting or function_parameter_count, or when a function has grown chains of if/else, nested conditionals or long switch statements.
---

# Complexity Refactoring

## Limits (enforced by `.swiftlint.yml`, run with `--strict`, so warnings fail the gate)

| Rule | Limit |
|---|---|
| `cyclomatic_complexity` | 10 per function |
| `function_body_length` | 40 lines |
| `closure_body_length` | 30 lines |
| `function_parameter_count` | 5 |
| `nesting` | 2 type levels, 2 function levels |

How SwiftLint 0.65.1 counts (measured, not assumed): +1 for each `if`, `guard`, `for`, `while`, `catch`, and each
`switch` case including `default`; a function with none scores 0. This is one lower than textbook McCabe
(decisions + 1): ten `if` statements report 10 and pass, eleven report 11 and fail.

SwiftLint does **not** count `&&`, `||`, the ternary operator, or `??`. Do not game the metric by rewriting
branches as ternaries or boolean chains: the logic is exactly as complex and harder to read. The goal is fewer
decisions per function, not a lower number.

Do not suppress these rules with `// swiftlint:disable`. If a limit genuinely cannot be met, stop and explain why to
the user instead of disabling the rule.

## Workflow

1. Write the behavior as tests first (Swift Testing), one test per rule or branch. These are the safety net for every
   refactoring step below.
2. Implement straightforwardly, then run SwiftLint. Do not pre-optimize structure you have not measured.
3. If a function exceeds a limit, apply the smallest move from the table below, re-run tests, re-run SwiftLint.
   Repeat until clean.
4. Never change behavior while reducing complexity. If tests must change, the refactoring was not behavior-preserving.

## Refactoring moves (pick the first that fits)

| Smell | Move |
|---|---|
| Preconditions nested around the main path | `guard` early exits |
| `if/else if` ladder choosing a value from thresholds | Ordered table + `first(where:)` |
| `if/else` or `switch` on a type code repeated in several places | Enum with a computed property per behavior |
| One function doing several sequential stages | Extract one `private` function per stage; the parent reads as the list of stages |
| Repeated optional-unwrapping branches | Optional chaining, `??`, `map`/`flatMap` |
| Boolean flag parameters changing behavior | Separate functions or an enum parameter |
| More than 5 parameters | A value type grouping the related parameters |
| Nested loops with filtering | `filter`/`map`/`reduce` or `contains(where:)` |

Extracting code into a helper only moves complexity; it is worth doing when each helper has one purpose and a name
that describes it. Do not create helpers that are called once and still contain the original tangle.

## Example: threshold ladder → ordered table

Before (complexity grows with every tier):

```swift
func volumeDiscount(quantity: Int) -> Double {
    if quantity >= 100 {
        return 0.15
    } else if quantity >= 50 {
        return 0.10
    } else if quantity >= 10 {
        return 0.05
    } else {
        return 0
    }
}
```

After (no branch statements; adding a tier adds data, not complexity):

```swift
struct VolumeTier {
    let minimumQuantity: Int
    let rate: Double
}

let volumeTiers = [
    VolumeTier(minimumQuantity: 100, rate: 0.15),
    VolumeTier(minimumQuantity: 50, rate: 0.10),
    VolumeTier(minimumQuantity: 10, rate: 0.05),
]

func volumeDiscount(quantity: Int) -> Double {
    volumeTiers.first { quantity >= $0.minimumQuantity }?.rate ?? 0
}
```

Keep tables sorted in the order they are matched and say so in a comment when the order matters.

## Example: type-code switches → enum behavior

Before (every caller repeats the switch):

```swift
func taxRate(regionCode: String) -> Double {
    switch regionCode {
    case "US": 0.07
    case "EU": 0.20
    default: 0
    }
}
```

After (the compiler forces every new region to define its rate):

```swift
enum Region {
    case unitedStates, europeanUnion, other

    var taxRate: Double {
        switch self {
        case .unitedStates: 0.07
        case .europeanUnion: 0.20
        case .other: 0
        }
    }
}
```

## Example: sequential stages → named steps

```swift
struct Order {
    let subtotal: Double
    let isMember: Bool
    let couponCode: String?
}

struct Checkout {
    func total(for order: Order) -> Double {
        let discounted = applyMemberDiscount(to: order.subtotal, isMember: order.isMember)
        let afterCoupon = applyCoupon(order.couponCode, to: discounted)
        return afterCoupon + shipping(for: afterCoupon)
    }

    private func applyMemberDiscount(to amount: Double, isMember: Bool) -> Double {
        isMember ? amount * 0.95 : amount
    }

    private func applyCoupon(_ code: String?, to amount: Double) -> Double {
        switch code?.uppercased() {
        case "SAVE10": amount * 0.9
        case "FLAT5": max(0, amount - 5)
        default: amount
        }
    }

    private func shipping(for amount: Double) -> Double {
        amount >= 50 ? 0 : 4.99
    }
}
```

Money in real code must use `Decimal`, not `Double`; `Double` keeps these examples short.

## Checklist before finishing

- [ ] SwiftLint `--strict` passes with no `swiftlint:disable` added.
- [ ] Every function reads top to bottom without scrolling; the main path is not indented inside conditionals.
- [ ] Rule tables and enums have tests covering each entry and the fallback.
- [ ] No behavior changed during refactoring (tests unchanged and green).
