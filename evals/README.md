# Harness evals

These evals measure whether a skill configuration changes the Swift that an agent writes.

The setup: each task is a small iOS 26 Swift package with a prompt. An agent (headless
`claude -p`) implements the task. Then `score.py` grades the result on:
- **Build:** the iOS 26.5 simulator build, counting warnings from the agent's `Sources/` only.
- **Hidden tests:** `HiddenTests`, a Swift Testing suite the agent never sees.
- **Lint:** the harness `.swiftlint.yml` with `--strict`.
- **Max complexity:** the highest cyclomatic complexity of any function.
- **Patterns:** per-task regex checks, either forbidden or required.

| Task | Probes |
|---|---|
| `pricing` | cyclomatic complexity in rule-heavy logic |
| `settings` | Observation vs `ObservableObject` |
| `token` | Keychain vs insecure storage. Hidden tests run on the macOS host, because simulator package tests lack the keychain entitlement (`-34018`). |
| `articles` | concurrency style under `defaultIsolation(MainActor)`: hops, `@concurrent`, unstructured Tasks |
| `catalog` | `NavigationStack` and value-based destinations |
| `notes` | accessible icon-only toolbar buttons, `ShareLink` |
| `config` | validation and error handling without crashes |

## Run
```sh
(cd tools/lint && swift package resolve)                 # pinned SwiftLint
python3 -I evals/tests/test_score_parsing.py             # fast unit tests
python3 -I evals/tests/test_transcript.py
python3 -I evals/tests/test_summarize.py
python3 -I evals/tests/test_references.py                # slow: validates every task with good/bad references
python3 -I evals/run_eval.py --configs none,upstream --repeats 2
python3 -I evals/summarize.py evals/results/<stamp>/results.json
```

## Isolation
- **Project settings only.** Runs use `--setting-sources project` and `--strict-mcp-config`.
- **Workspaces outside `~`.** They live under `/private/tmp/ios-harness-evals/`. A smoke run
  showed that a workspace inside the home directory picks up `~/.claude/CLAUDE.md` through
  ancestor-directory discovery. The agent then read the user's personal directives.
- **Outside-access guard.** Every tool call that references a path outside the workspace is
  recorded as `outside_access`. Treat any run with a non-empty value as contaminated.
- Claude Code's built-in skills (e.g. `dataviz`, `code-review`) are still present. They are the same
  for every config.

## Limitations: read before drawing conclusions
- **Small n.** With 2 repeats per cell, results show *direction*, not significance.
- **Regex checks are approximate.** Each one is validated against good and bad reference solutions
  (`test_references.py`), but an unusual shape of code can evade or trip them.
- **Shallow functional coverage for UI tasks.** Hidden tests for those mostly check the public API
  and model logic. Visual and VoiceOver behavior isn't exercised.
- **Skills may not load.** An agent may never load a skill. `skills_used` records whether it did.
  A config with no loaded skill is effectively the baseline.
- **Fixed model.** Default is `claude-opus-5-5`. Other models may respond to skills differently.
