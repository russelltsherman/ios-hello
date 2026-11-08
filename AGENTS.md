# Agent directives: iOS app

These rules apply to every coding agent working in this repository. Gates enforce them (see Definition of done).
Skills in `.claude/skills/` have the details. Load the matching skill before writing code in its area.

## Baseline
- Xcode 27, Swift 6.4 toolchain, **Swift 6 language mode**, **iOS 26 deployment target**.
- APIs newer than iOS 26 require `#available` with a fallback. Do not raise the deployment target.
- SwiftUI first. UIKit only when SwiftUI has no equivalent, isolated behind a representable.
- No new third-party dependencies without asking the user.

## Skills to load
| Working on | Skill |
|---|---|
| Any Swift code | `swift-idioms` |
| New feature, module, dependency, navigation | `architecture` |
| SwiftUI views | `swiftui` |
| async/await, actors, Sendable, isolation warnings | `swift-concurrency` |
| Branching business rules, SwiftLint complexity/length findings | `complexity-refactoring` |
| Tokens, personal data, files, networking config, logging, URLs from outside, Info.plist / privacy manifest | `ios-security` |
| Tests | `swift-testing` |

## Non-negotiables
- **Tests first.** Write or update a failing Swift Testing test that describes the behavior, then make it pass.
  Bug fixes start with a test that reproduces the bug.
- **No force operations** in `Sources/`: no `!` unwrap, `try!`, `as!`, or IUO.
- **Observation only.** No `ObservableObject`/`@Published`/`@StateObject`/`@ObservedObject`/`@EnvironmentObject`.
- **Secrets only in the Keychain.** Never in UserDefaults, files, logs, source or the bundle.
- **No silenced diagnostics.** Never add `swiftlint:disable`, `@preconcurrency`, `@unchecked Sendable`,
  `nonisolated(unsafe)` or `// swift-format-ignore` to make a gate pass. If a rule can't be met, stop and explain.
- **Keep changes scoped** to the request. Suggest unrelated modernization separately; don't apply it.

## Definition of done
A task is not done until all of these pass locally:
```sh
scripts/verify            # swift-format lint, SwiftLint --strict, build with warnings as errors, tests
```
Report the actual output. If something fails or a step was skipped, say so plainly.

## Repository map
- `App/`: composition root. `Packages/Core/*`: shared modules. `Packages/Features/*`: one module per feature.
- `.swiftlint.yml`, `.swift-format`: the style and complexity gates. Do not edit them to make code pass.
- `evals/`, `tools/`: the harness's own test infrastructure.
