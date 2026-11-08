# Upstream

- Source: https://github.com/AvdLee/Swift-Testing-Agent-Skill (`swift-testing-expert/`)
- Commit: 798e9b1a2bcac164d4f0c781908199e754f0bab6
- License: MIT (see `LICENSE`, copyright retained)

## Changes in this fork
1. Renamed the skill `swift-testing-expert` → `swift-testing`.
2. Fixed `references/traits-and-tags.md`: `.timeLimit(.seconds(10))` does not compile, because `TimeLimitTrait`
   only accepts minutes. Changed to `.timeLimit(.minutes(1))` and documented the constraint. Found by
   `tools/snippet_check.py`.
3. Added "Project rules": TDD workflow, Swift Testing default, model testing with fake clients, distinct
   helper names, and reporting real results. The helper-name rule comes from an eval: hidden and agent
   test helpers both named `StubClient` collided.
