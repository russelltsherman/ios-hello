"""Summarize an eval results.json into a Markdown comparison table.

Usage: python3 -I evals/summarize.py evals/results/<stamp>/results.json
Values are means over repeats; n is shown so small samples are not mistaken for strong evidence.
"""
import collections
import json
import pathlib
import statistics
import sys

COLUMNS = [
    ("hidden pass", lambda r: r["hidden_passed"] / r["hidden_total"] if r["hidden_total"] else 0, "{:.0%}"),
    ("build", lambda r: 1.0 if r["build_ok"] else 0.0, "{:.0%}"),
    ("warnings", lambda r: r["source_warnings"], "{:.1f}"),
    ("lint", lambda r: r["lint_violations"], "{:.1f}"),
    ("max CC", lambda r: r["max_complexity"], "{:.1f}"),
    ("forbidden", lambda r: sum(r["forbidden"].values()), "{:.1f}"),
    ("req. missing", lambda r: len(r["required_missing"]), "{:.1f}"),
    ("cost $", lambda r: r.get("agent_cost_usd") or 0, "{:.2f}"),
]


def group(results: list[dict]) -> dict[tuple[str, str], list[dict]]:
    groups: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for result in results:
        groups[(result["task"], result["config"])].append(result)
    return dict(sorted(groups.items()))


def table(results: list[dict]) -> str:
    header = ["task", "config", "n", *(name for name, _, _ in COLUMNS), "skills used", "outside access"]
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for (task, config), runs in group(results).items():
        cells = [fmt.format(statistics.mean(fn(r) for r in runs)) for _, fn, fmt in COLUMNS]
        used = collections.Counter(s for r in runs for s in r.get("skills_used", []))
        outside = sum(bool(r.get("outside_access")) for r in runs)
        skills = ", ".join(f"{name}×{count}" for name, count in sorted(used.items())) or "—"
        lines.append("| " + " | ".join([task, config, str(len(runs)), *cells, skills, str(outside)]) + " |")
    return "\n".join(lines)


def details(results: list[dict]) -> str:
    """Per-pattern forbidden counts, lint rules and task metrics, summed over repeats."""
    out = []
    for (task, config), runs in group(results).items():
        merged: dict[str, collections.Counter] = {"forbidden": collections.Counter(),
                                                  "lint": collections.Counter(),
                                                  "metrics": collections.Counter()}
        for r in runs:
            merged["forbidden"].update({k: v for k, v in r["forbidden"].items() if v})
            merged["lint"].update(r["lint_by_rule"])
            merged["metrics"].update({k: v for k, v in r["metrics"].items() if v})
        parts = [f"{kind}: " + ", ".join(f"{k}={v}" for k, v in sorted(c.items()))
                 for kind, c in merged.items() if c]
        out.append(f"- **{task} / {config}** (n={len(runs)}): " + ("; ".join(parts) or "clean"))
    return "\n".join(out)


def main() -> None:
    results = json.loads(pathlib.Path(sys.argv[1]).read_text())
    print(table(results))
    print("\nTotals summed over repeats:\n")
    print(details(results))


if __name__ == "__main__":
    main()
