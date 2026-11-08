# iOS Agent Harness — Plan & Status

Last updated: 2026-10-14. This is the working copy and is updated as the work proceeds.

## Goal
A per-repo project template that makes coding agents produce idiomatic, secure, low-complexity Swift.
- **Guidance:** skills and AGENTS.md.
- **Deterministic enforcement:** pinned SwiftLint and swift-format, warnings-as-errors builds, hooks.
- **Verification:** tests are the definition of done, plus review agents.

## Decisions
| Topic | Decision |
|---|---|
| Packaging | Per-repo template |
| Baseline | Xcode 27 / Swift 6.4 toolchain, Swift 6 language mode; **iOS 26 and macOS 26** deployment targets; newer APIs behind `#available`; SwiftUI-first |
| Multi-platform packages | verify tests the primary (first-declared) platform only |
| Architecture | MV/MVVM hybrid: `@Observable` feature models only where there is real logic, thin views, SPM feature modules, protocol dependency clients |
| SwiftLint | 0.65.1 via SwiftLintPlugins SPM, pinned (`tools/lint/Package.resolved`) |
| Skills | Fork MIT sources after evaluation; write our own where there are gaps; Apple skills exported locally, never committed (no license) |
| Concurrency stance | **Pending measurement**: MainActor default with `@concurrent` services vs AvdLee's `@concurrent`-Task rule (eval task `articles`) |
| Evals | Small pilot: 7 tasks × {none, upstream, fork} × 2 repeats |

## Status
| # | Step | Status | Where |
|---|---|---|---|
| 1 | Export Apple skills, check licenses | Done | `docs/research/skill-evaluation.md` |
| 2 | Score candidates (license, size, compile check, read-through) | Done | same |
| 3a | Snippet compile checker + test | Done | `tools/snippet_check.py`, `tools/tests/` |
| 3b | Lint/format configs, verified compatible | Done | `.swiftlint.yml`, `.swift-format`, `tools/tests/test_lint_gate.py` |
| 3c | Eval suite (7 tasks, scorer, runner, references) | Done | `evals/` |
| 3d | Pilot run: none vs upstream (28 runs) | Done. **Skills were never loaded**; baseline errors are lint-class only | `docs/research/pilot-results.md` |
| 4a | Write our own skills: complexity-refactoring, swift-idioms | **Drafted**; examples compile clean | `.claude/skills/` |
| 4b | Write our own skills: ios-security, architecture | **Drafted**; examples compile clean (also under MainActor isolation) | `.claude/skills/` |
| 4c | Forks: swift-testing **done**; swiftui, swift-concurrency to do | In progress | `.claude/skills/` + `UPSTREAM.md` each |
| 5 | AGENTS.md / CLAUDE.md directives (with explicit skill routing) | **Drafted** | `AGENTS.md`, `CLAUDE.md` |
| 6 | `scripts/verify` gate (tested: 5 cases) **done**; hooks + settings.json next (top priority per pilot) | In progress | `scripts/verify`, `.claude/` |
| 7 | Review subagents (swift-reviewer, security-auditor) | To do | `.claude/agents/` |
| 8 | "harness" config eval (routing + skills, then + hooks), harder tasks, forced-load concurrency comparison | To do | `evals/` |
| 9 | CI workflow running the same gates | To do | `.github/workflows/` |
| 10 | macOS hello world (dogfood): `Greeter` + `GreetingView` (TDD), `HelloMac` executable | **Built**; tests green | `docs/PLAN-hello-mac.md`, `App/HelloMac`, `Packages/Features/Greeting` |
| 11 | verify: primary-platform destination, `App/` scan, fail when zero tests ran | **In progress** (tests written first) | `scripts/verify`, `tools/tests/test_verify.py` |
| 12 | Platform-aware harness, rest of Part B: snippet checker `--platform`, AGENTS.md baseline table, swiftui macOS section, architecture app shells, evals `platform` | Deferred | `docs/PLAN-hello-mac.md` §B |
| 13 | Rename `ios-security` → `apple-security` with per-platform sections (verify macOS claims against Apple docs first) | Deferred | `.claude/skills/` |

## Findings that shaped the plan
- **dpearson2699/swift-ios-skills is PolyForm Perimeter** (noncompete), not MIT. Reading only.
- **Compile defects in upstream skills.**
  - AvdLee testing: `.timeLimit(.seconds)` doesn't compile.
  - AvdLee concurrency: `Thread.current` examples contradict the skill's own text, and the main
    Task example trips a Swift 6.4 warning.
- **SwiftLint counting (measured).** It counts `if`, `guard`, `for`, `while`, `catch` and each
  `case`. It does not count `&&`, `||`, `?:` or `??`. *n* branches score *n*.
- **Keychain in simulator package tests fails with `-34018`.** The token eval runs its tests on the
  macOS host.
- **Eval isolation.** Workspaces under `~` load `~/.claude/CLAUDE.md` through ancestor discovery, so
  workspaces live in `/private/tmp/ios-harness-evals/`, guarded by `outside_access`.

## Verification
- `python3 -I -m unittest discover -s tools/tests`: checker and lint gate.
- `python3 -I evals/tests/test_references.py`: every eval task validated against good and bad references.
- Every skill must pass `tools/snippet_check.py` with zero warnings or errors in its positive examples.
