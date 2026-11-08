# Skill Evaluation — Candidate Sources for the iOS Agent Harness

Date: 2026-10-14 · Toolchain: Xcode 27.0 (27A266a), Swift 6.4 · Harness target: iOS 26, Swift 6 mode

## Method
1. **License check**: read each repo's LICENSE file, not just the skill frontmatter.
2. **Structure and size**: word counts for each SKILL.md and for the total including references.
3. **Compile check** with `tools/snippet_check.py`:
   - Every ```swift block is extracted and typechecked standalone.
   - Settings: Swift 6 mode, iOS 26 simulator SDK, Swift Testing macros enabled.
   - Blocks the skill labels as anti-patterns (❌, "avoid", "before"…) are counted separately.
   - Most failures are just fragments that reference undefined symbols, so only API, availability
     and deprecation errors and compiler warnings count as defects.
   - **Limit:** this catches compile-level defects only. It says nothing about whether the advice
     is semantically correct.
4. **Manual read** of each SKILL.md and a sample of references, scored against the rubric:
   accuracy, currency, internal consistency, LLM-failure focus, token cost, overlap, license,
   maintenance.

## License (decisive for forking)
| Source | License (from LICENSE file) | Fork? |
|---|---|---|
| Apple Xcode 27 skills (`xcrun mcpbridge run-agent skills export`) | **No license text in the export** | **No.** Install them locally with an export script and don't commit them. |
| twostraws/SwiftUI-Agent-Skill `swiftui-pro` @f980071 | MIT | Yes |
| AvdLee/SwiftUI-Agent-Skill @204dba7 | MIT | Yes |
| AvdLee/Swift-Concurrency-Agent-Skill @d577081 | MIT | Yes |
| AvdLee/Swift-Testing-Agent-Skill @798e9b1 | MIT | Yes |
| dpearson2699/swift-ios-skills @8d90fd1 | **PolyForm Perimeter 1.0.0** (noncompete). One skill's frontmatter says "MIT", which contradicts the repo LICENSE. | **No.** A harness that bundles iOS skills could count as a "competing product". Use it for reading only. (Not legal advice.) |

## Size (words; a token count is roughly 1.3× this)
| Skill | SKILL.md | Total incl. references |
|---|---|---|
| Apple swiftui-specialist | 656 | 22,716 |
| Apple modernize-tests | 1,322 | 1,322 |
| Apple audit-xcode-security-settings | 8,173 | 19,094 |
| swiftui-pro | 807 | 10,369 |
| AvdLee swiftui-expert-skill | 1,544 | 47,718 |
| AvdLee swift-concurrency | 1,774 | 30,707 |
| AvdLee swift-testing-expert | 612 | 5,620 |

## Compile-check results (positive examples only)
| Skill | Blocks | Clean | Defects found |
|---|---|---|---|
| Apple swiftui-specialist | 71 | 20 | **0.** The one warning is a deliberate anti-pattern example. |
| swiftui-pro | 8 | 0 (fragments) | 2. iOS 27-only reorder APIs with no `#available` (correct for its iOS 27 default). |
| AvdLee swiftui-expert | 330 | 45 | 13 total. 6 are iOS 27-only Document APIs with no gating. 7 are macOS-only APIs (irrelevant for iOS). |
| AvdLee swift-concurrency | 303 | 38 | 7 `Thread.current` uses in `threading.md`. **The same file says this fails to compile in Swift 6.** |
| AvdLee swift-testing | 42 | 29 | 1. `.timeLimit(.seconds(10))` does not compile; the time limit is minutes-only. |

**Verified separately:**
- The swift-concurrency SKILL.md canonical example, `Task { @concurrent in … try await … }` with
  the result discarded, raises the Swift 6.4 warning `NoUseUnstructuredThrowingTask`. It fails a
  warnings-as-errors build.
- The swift-testing claim that "`@available` on a suite is an error" is **correct**, confirmed by
  compiling it.

## Qualitative assessment
- **Apple swiftui-specialist.**
  - Narrow scope: data flow, environment, ForEach identity, localization, soft deprecation.
  - Highest accuracy of any source here, and very cheap at the router level.
  - It states that it "unconditionally supersedes prior training", which is a strong prompt to
    keep in mind if it conflicts with our forks.
  - No accessibility, navigation, or architecture coverage.
- **Apple audit-xcode-security-settings.**
  - Strong build-hardening content: Enhanced Security, compiler warnings, the analyzer.
  - Depends heavily on Xcode MCP tools (XcodeGlob, XcodeUpdate…) and forbids using Bash
    alternatives. It works best inside Xcode's agent and less well from the CLI.
  - Explicitly skips ATS, TLS, signing, and privacy.
- **swiftui-pro.**
  - Concise and review-oriented, with a clear output format.
  - Targets the failure modes LLMs actually have: accessibility, deprecated APIs, `Binding(get:set:)`.
  - Respects the project deployment target, but **defaults new apps to iOS 27** and Swift 6.4,
    so the fork needs a baseline edit.
- **AvdLee swiftui-expert.**
  - The broadest coverage: layout, navigation, accessibility, Liquid Glass, Instruments scripts.
  - The most expensive (~48k words).
  - Still teaches `@StateObject`/`@ObservedObject` rules that our iOS 26 baseline doesn't need.
  - Contains macOS material.
  - Deliberately takes no position on architecture.
- **AvdLee swift-concurrency.**
  - Strong diagnostic routing.
  - Good guardrails: no blanket `@MainActor`; any escape hatch needs a documented invariant.
  - However, its "start Tasks `@concurrent`" advice adds `MainActor.run` hops. With
    `defaultIsolation(MainActor)` plus `@concurrent` services, the simpler `Task { let x = try
    await service.fetch(); apply(x) }` doesn't block the main actor. This is **my judgment, not
    verified by measurement**.
  - It also has the compile defects listed above.
- **AvdLee swift-testing.**
  - Compact and sound.
  - One compile defect.
  - Overlaps with Apple's modernize-tests, which is better for migrating from XCTest.

## Recommended fork / author matrix
| Harness skill | Basis | Changes required |
|---|---|---|
| `swiftui` (review + authoring) | Fork **swiftui-pro** as the spine. Pull selected references from AvdLee: layout, navigation, accessibility, Liquid Glass. | Default iOS 26 with iOS 27 behind `#available`. Remove ObservableObject and macOS material. Encode the MV/MVVM-hybrid stance. |
| (Apple swiftui-specialist, swiftui-whats-new-27, modernize-tests, audit-xcode-security-settings) | **Not vendored.** `scripts/install-apple-skills` exports them locally (gitignored). | Document how they take precedence over, and conflict with, our forks. |
| `swift-concurrency` | Fork AvdLee, trimmed hard. | Fix the `Thread.current` examples and the discarded-throwing-Task example. Align with `defaultIsolation(MainActor)` + `@concurrent` services. Cut the course links. |
| `swift-testing` | Fork AvdLee. | Fix `.timeLimit`. Add TDD workflow rules: test first, red/green evidence. |
| `swift-idioms` | **Author.** | API Design Guidelines, value semantics, access control, typed throws, no force-unwrap/`try!`, error modeling. |
| `complexity-refactoring` | **Author.** No good source found. | CC thresholds tied to SwiftLint config. Refactoring moves: guard/early exit, table-driven code, enum polymorphism, extracting pure functions. Before/after examples that compile. |
| `ios-security` | **Author.** Use dpearson as reading material only; do not copy it. | MASVS mapped to iOS APIs: Keychain (with correct OSStatus handling), ATS, CryptoKit, privacy manifest, logging redaction. Every snippet compile-checked. |
| `architecture` | **Author.** | MV/MVVM hybrid, SPM module layout, dependency clients, navigation router, test seams. |

## Harness requirement derived from this evaluation
Every skill in the harness, forked or authored, must pass `tools/snippet_check.py` in CI.
- Positive examples must typecheck under iOS 26 / Swift 6, or be explicitly marked as fragments.
- Positive examples must not produce warnings.

This is the cheapest way to keep the defect classes found above out of the harness.

## Not yet done
- **Behavioral evals.** These measure whether an agent with a skill actually writes better code.
  They need headless agent runs, which cost money and time, so they need approval first.
- **Semantic review of every reference file.** Only the SKILL.md files and a sample of references
  were read.
