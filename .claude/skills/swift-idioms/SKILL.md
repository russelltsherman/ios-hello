---
name: swift-idioms
description: Idiomatic Swift 6 rules for this project - naming per the Swift API Design Guidelines, value vs reference types, optionals without force-unwrapping, error handling, access control, and Codable. Use whenever writing, reviewing or refactoring any non-UI Swift code (models, services, parsing, utilities), and when SwiftLint reports force_unwrapping, force_try, force_cast, implicitly_unwrapped_optional or identifier_name.
---

# Swift Idioms

Project baseline: Swift 6.4 toolchain, Swift 6 language mode, iOS 26 deployment target. Concurrency rules live in the
`swift-concurrency` skill, SwiftUI rules in `swiftui`, architecture in `architecture`.

## Hard rules (gate-enforced or always bugs)

- No `!` force-unwrap, `try!`, `as!`, or implicitly unwrapped optionals (`Type!`) in `Sources/`. Tests may use
  `try #require(...)` instead.
- No `fatalError`/`preconditionFailure` for conditions caused by input, network, disk or user data. Throw instead.
  They are acceptable only for programmer errors that tests would catch (e.g. an exhaustive `switch` over a
  value the code itself constructed), and then with a message.
- Never discard errors silently: no empty `catch {}`, and `try?` only when "absent" is a correct, intended outcome.
- No `Any`/`AnyObject` in APIs where a concrete type, generic or protocol works.
- No Objective-C legacy types (`NSString`, `NSArray`, `NSDictionary`, `NSNumber`) in Swift APIs.

## Naming (Swift API Design Guidelines)

- Name for clarity at the call site: `remove(at:)`, `insert(_:at:)`, `distance(to:)`.
- Omit needless words: `removeElement(_:)` → `remove(_:)`.
- Booleans read as assertions: `isEnabled`, `hasPendingChanges`, `canUndo`.
- Mutating/non-mutating pairs: `sort()`/`sorted()`, `formUnion(_:)`/`union(_:)`.
- Factory methods start with `make`: `makeIterator()`.
- Types and protocols are `UpperCamelCase`; protocols describing a capability end in `-able`/`-ing`
  (`Equatable`, `ProgressReporting`), protocols describing a thing are nouns (`Collection`).
- No type-name prefixes (`ABCUser`) and no Hungarian notation.

## Types

- Default to `struct` and `enum`. Use `final class` only for identity, shared mutable state behind isolation
  (`@MainActor`/actor), reference semantics required by an API, or `@Observable` models.
- Mark classes `final` unless designed for subclassing.
- Prefer `let`. Make stored properties `private(set)` or `private` unless callers must write them.
- Model states as enums with associated values instead of combinations of optionals and booleans:

```swift
enum Upload {
    case idle
    case uploading(progress: Double)
    case finished(URL)
    case failed(String)
}
```

- Use domain types instead of raw primitives where mix-ups are plausible:

```swift
struct UserID: Hashable, Sendable {
    let rawValue: String
}

struct OrderID: Hashable, Sendable {
    let rawValue: String
}

func cancel(order: OrderID, requestedBy user: UserID) {}
```

## Optionals

Unwrap with `guard let`, `if let`, optional chaining, `??`, or `map`. Prefer the shorthand `if let value`.

```swift
import Foundation

func avatarURL(from string: String?) -> URL? {
    guard let string, let url = URL(string: string), url.scheme == "https" else {
        return nil
    }
    return url
}
```

For literals that are known-valid at compile time, avoid the force-unwrap with a static fallback rather than `!`:

```swift
import Foundation

enum Endpoints {
    static let base = URL(string: "https://api.example.com") ?? URL(filePath: "/")
}
```

Better still, when a value may legitimately be invalid (config, user input), make the initializer `throw`.

## Errors

- Throw specific error types callers can act on; include the context needed to recover or report.
- Use untyped `throws` by default. Use typed throws (`throws(MyError)`) when the error set is closed and callers are
  expected to handle every case exhaustively (validation, parsing, a module's internal boundary).
- Map lower-level errors at module boundaries instead of leaking implementation types.

```swift
import Foundation

enum ProfileError: Error, Equatable {
    case missingName
    case invalidAge(Int)
}

struct Profile: Equatable {
    let name: String
    let age: Int

    init(name: String, age: Int) throws(ProfileError) {
        let trimmed = name.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { throw .missingName }
        guard (0...150).contains(age) else { throw .invalidAge(age) }
        self.name = trimmed
        self.age = age
    }
}
```

## Access control

- Start `private`; widen only when needed. `fileprivate` is rarely the right answer.
- In SPM modules, mark only the intended API `public`. Do not make everything `public` to "fix" a compile error;
  use `@testable import` in tests instead.
- Extensions that implement a protocol conformance go in their own `extension Type: Protocol {}` block.

## Codable

- Let the compiler synthesize `Codable` whenever names match; use `CodingKeys` only for renames.
- Decode into a private DTO, then validate into the domain type. Never let unvalidated payloads into the domain.
- Configure `JSONDecoder` (`dateDecodingStrategy`, `keyDecodingStrategy`) once, in one place.

```swift
import Foundation

struct Account: Equatable {
    let email: String
    let createdAt: Date
}

enum AccountDecodingError: Error {
    case invalidEmail(String)
}

private struct AccountDTO: Decodable {
    let email: String
    let createdAt: Date
}

func decodeAccount(from data: Data) throws -> Account {
    let decoder = JSONDecoder()
    decoder.dateDecodingStrategy = .iso8601
    let dto = try decoder.decode(AccountDTO.self, from: data)
    guard dto.email.contains("@") else { throw AccountDecodingError.invalidEmail(dto.email) }
    return Account(email: dto.email, createdAt: dto.createdAt)
}
```

## Collections and functional style

- `first(where:)`, `contains(where:)`, `isEmpty`, `allSatisfy` over manual loops and `count == 0`.
- `map`/`filter`/`compactMap`/`reduce(into:)` when they read more clearly than a loop; a plain `for` loop is fine
  when it is clearer, especially with side effects.
- Never mutate a collection while iterating it.

## Checklist before finishing

- [ ] `swiftlint lint --strict` passes; no new `swiftlint:disable`.
- [ ] No force operations, IUOs, or silent `try?`/empty `catch` in `Sources/`.
- [ ] New types default to value semantics; classes are `final`.
- [ ] Public surface is minimal and intentional.
- [ ] Every thrown error is tested (Swift Testing `#expect(throws:)`).
