# Plan: macOS Hello World (harness dogfood) + making the harness platform-aware

> Working copy of the approved plan; status is tracked in `docs/PLAN.md`.

## Context
Russell wants a hello-world Swift app that targets **macOS**, built **inside the harness repo**
(`/Users/russelltsherman/src/iOS`). The point is to dogfood the harness end to end:
- `AGENTS.md` routing and the skills
- TDD
- `scripts/verify`

The harness currently assumes **iOS 26** everywhere, so a macOS app forces the question of making it
platform-aware. Russell asked to discuss that first (Part B).

Decided:
- **App form:** SPM executable plus a feature library. It is fully CLI-buildable and testable, runs
  with `swift run`, and has no .app bundle, signing or sandbox.
- **Target:** macOS 26.

## Part A: Hello World (decided scope)
Layout, following the `architecture` skill:
```
App/HelloMac/Package.swift          # executableTarget "HelloMac" (composition root only), depends on Greeting
App/HelloMac/Sources/HelloMac/HelloMacApp.swift
Packages/Features/Greeting/Package.swift   # library "Greeting" + test target
Packages/Features/Greeting/Sources/Greeting/Greeting.swift      # pure logic
Packages/Features/Greeting/Sources/Greeting/GreetingView.swift  # SwiftUI view
Packages/Features/Greeting/Tests/GreetingTests/GreetingTests.swift
```

- **Behavior (gives the test something real to check):**
  - `Greeting.message(for name: String?) -> String` returns "Hello, World!" for nil or blank input.
  - Otherwise it returns "Hello, <trimmed name>!".
  - `GreetingView` has a `TextField` for the name and a `Text` showing the message, with `@State` local only.
    There's no feature model, because there's no logic beyond that pure function (architecture skill principle 2).
- **Package settings:**
  - `platforms: [.macOS(.v26)]`
  - Swift 6 mode
  - `.defaultIsolation(MainActor.self)` for the app and the feature module
- **TDD order:** write `GreetingTests` first (nil, blank, trimmed name, parameterized cases), see them fail, then
  implement.
- **SPM-run caveat (unverified):**
  - A SwiftUI `App` launched from a bare executable may not activate or show in the Dock without
    `NSApplication.shared.setActivationPolicy(.regular)`.
  - I'll check this by running it, and add the call only if it's needed.

## Part B: Making the harness platform-aware (for discussion)
| Area | Today | Platform-aware change |
|---|---|---|
| `scripts/verify` | iOS simulator only; scans `Packages/` | Read each package's platforms (`swift package dump-package`); iOS → simulator destination, macOS → `platform=macOS`; scan `App/` too. Extend `tools/tests/test_verify.py` with a macOS-package case. |
| `tools/snippet_check.py` | iOS simulator SDK only | `--platform ios|macos`. Skills declare `metadata.platforms`, and CI checks each snippet on each declared platform. |
| `AGENTS.md` | "iOS 26 deployment target", "UIKit only…" | A per-platform baseline table (iOS 26, macOS 26) and "UIKit/AppKit only when SwiftUI lacks an equivalent". |
| `ios-security` | iOS Keychain and file protection | Rename to `apple-security`, with macOS notes: `kSecUseDataProtectionKeychain`, App Sandbox, Hardened Runtime. **Verify with Apple docs before writing:** file-protection effect on macOS, and privacy-manifest scope. |
| `swiftui` fork (not built) | swiftui-pro is iOS-centric | Add a macOS section forked from AvdLee's MIT `macos-scenes`, `macos-views` and `macos-window-styling` references. |
| `architecture` | iOS-flavored layout | An app-shell section per platform (SPM executable vs Xcode app). |
| Neutral already | swift-idioms, complexity-refactoring, swift-testing, `.swiftlint.yml`, `.swift-format` | Baseline wording only. |
| `evals/score.py` | iOS simulator hard-coded | A per-task `platform` field; a macOS eval task later. |

**Decisions (2026-10-14):**
- **Hello world first.** Change the harness only where the app breaks it. We already know `scripts/verify` will
  break, because it hard-codes the iOS simulator and doesn't scan `App/`.
- **Multi-platform packages:** verify tests the **primary (first-declared) platform only**.
- **Security skill:** rename `ios-security` → `apple-security` with per-platform sections. This happens in a later
  step, and the macOS claims get verified against Apple docs first.
- **Later steps:** the rest of Part B (snippet checker platforms, AGENTS.md table, swiftui macOS section,
  architecture app shells, evals) is a separate step after the hello world. It gets recorded in `docs/PLAN.md`.

## Implementation order
1. Build the app (Part A). Write `GreetingTests` first and see them fail. Implement `Greeting` and `GreetingView`,
   then the `HelloMac` executable. Get `swift test` and `swift build` green in each package.
2. Run `scripts/verify`. It's expected to fail on the iOS destination and the missing `App/` scan.
3. Adapt verify, test-first:
   - Add cases to `tools/tests/test_verify.py`: a macOS-only package passes, a macOS warning fails, and a
     package under `App/` gets verified.
   - Then implement: read the platforms from `swift package dump-package`; for the primary platform, use
     `platform=macOS` for macOS and keep the iOS simulator default for iOS; scan `App/` as well as `Packages/`.
4. Confirm the existing 5 verify cases still pass.
5. Launch with `swift run`. Add the activation-policy call only if the window doesn't come forward.
6. Copy this plan to `docs/PLAN-hello-mac.md`. Add rows to `docs/PLAN.md` for the deferred platform work and the
   `apple-security` rename.

## Verification
- `python3 -I tools/tests/test_verify.py`: existing 5 cases plus new macOS cases (clean macOS package passes,
  macOS warning fails).
- `swift test` in `Packages/Features/Greeting`: the tests are red first, then green.
- `scripts/verify` at the repo root: format, lint, build with warnings as errors, and tests for both packages.
- `swift run --package-path App/HelloMac`: the window shows "Hello, World!" and updates as a name is typed.
  I'll confirm it launches; I'll ask you to look at the window, since I can't see the screen reliably.
