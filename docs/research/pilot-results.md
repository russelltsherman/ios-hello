# Eval Pilot 1: no skills vs upstream skills

Run: `evals/results/20261014-123150/` · Model: claude-opus-5-5 · 7 tasks × 2 configs × 2 repeats = 28 runs ·
Total agent cost ≈ $8.4.

The `articles` and `settings` rows were rescored after a task bug was fixed (`evals/rescore.py`). The hidden-test
helper `StubClient` collided with helpers the agents wrote themselves, which produced false 0/3 results. Helpers are
now prefixed `Hidden`.

## Headline: the upstream skills were never used
- **No skill was loaded in any of the 14 upstream runs.** There was no `Skill` tool call and no `Read` of any
  `.claude/skills/` file. The agents saw the files in a directory listing and ignored them.
- That includes `swiftui-pro`, whose description says "Use when reading, writing, or reviewing SwiftUI projects",
  on four SwiftUI tasks.
- **Consequence:** this pilot compared the baseline against itself. It says nothing about skill *content*.
- **Implication for the harness:** skills placed in `.claude/skills/` don't get used just because they exist and
  their descriptions match. The harness needs:
  1. **Explicit routing in `AGENTS.md`** ("load skill X when working on Y"). It's now drafted.
  2. **Deterministic enforcement** that doesn't depend on whether the agent loaded anything.

## What the baseline model actually gets wrong
Every run in both configs did the following:
- **Functionally:** built cleanly, passed all hidden tests, produced 0 compiler warnings.
- **Patterns the tasks were designed to catch:** used `@Observable` (no `ObservableObject`), `NavigationStack` with
  value destinations, labeled icon buttons with `ShareLink`, a Keychain with explicit `ThisDeviceOnly`
  accessibility, and no `DispatchQueue`.

The defects that remained are all things the lint gate catches mechanically:

| Defect | Where | Count (summed over 4 runs) |
|---|---|---|
| `force_unwrapping` | pricing (`Decimal(string: "0.07")!`) | 25 |
| `line_length` | config, articles | 5 |
| `async_without_await` | articles | 2 |
| `closure_body_length` | notes | 1 |

Max cyclomatic complexity stayed between 1 and 8. No run exceeded the limit of 10.

## Concurrency stance: unresolved
- **What happened:** none of the 8 runs (baseline or upstream) used `MainActor.run` or `@concurrent`. Every run used
  a plain `Task { await model.load() }` or `.task {}` under `defaultIsolation(MainActor)`, and none produced a
  warning.
- **Why it doesn't settle anything:** the AvdLee skill was never loaded, so its `@concurrent` Task rule was never
  tested.

## Caveats
- **n = 2 per cell, and one model.** These results show direction only.
- **The tasks may be too easy for this model.** The seeded anti-patterns reflect older models. Harder or longer
  tasks (multi-file features, refactoring existing bad code) may expose more.
- **The outside-access guard flagged 9 runs, all harmless:** `/tmp/*-dd` derived-data paths the agents chose,
  Claude Code's own background-task output files, `~/Library/Logs/DiagnosticReports`, and an `/etc/hosts` string.
  None touched user configuration. The guard is deliberately broad.

## Changes to the plan
1. **The next config is "harness"**, not just "fork". It includes `AGENTS.md`/`CLAUDE.md` routing, our skills, and
   hooks. Ablations isolate the parts: routing + skills without hooks, and the full harness.
2. **Hooks become first priority.** The only defects observed are lint-class, and a post-edit lint hook fixes those
   regardless of skill use.
3. **Add harder tasks**, such as refactoring an existing messy file or a multi-screen feature, so skill content has
   something to improve on.
4. **Concurrency stance needs a forced-load run.** Instruct the agent to load `swift-concurrency` and compare the
   upstream text against our fork on `articles`.
