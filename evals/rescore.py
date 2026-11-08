"""Re-score existing eval workspaces after a task or scorer fix, without re-running agents.

Usage: python3 -I evals/rescore.py evals/results/<stamp> [--tasks articles,settings]
Workspaces are found under run_eval.WORK_ROOT/<stamp>/. Agent fields (cost, skills, outside_access)
are kept; score fields are replaced. results.json is rewritten.
"""
import argparse
import json
import pathlib
import shutil
import sys

EVALS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(EVALS))
import run_eval  # noqa: E402
import score  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results_dir", type=pathlib.Path)
    parser.add_argument("--tasks", default="")
    args = parser.parse_args()
    selected = set(filter(None, args.tasks.split(",")))
    all_results = []
    for score_file in sorted(args.results_dir.glob("*/*/*/score.json")):
        previous = json.loads(score_file.read_text())
        if selected and previous["task"] not in selected:
            all_results.append(previous)
            continue
        task_dir = EVALS / "tasks" / previous["task"]
        workspace = run_eval.WORK_ROOT / args.results_dir.name / previous["task"] / previous["config"] / str(previous["rep"])
        shutil.rmtree(workspace / ".derived", ignore_errors=True)
        agent_fields = {k: v for k, v in previous.items() if k.startswith("agent_") or k in
                        ("task", "config", "rep", "skills_used", "outside_access")}
        updated = {**agent_fields, **score.score(task_dir, workspace)}
        score_file.write_text(json.dumps(updated, indent=2))
        print(f"{previous['task']}/{previous['config']}/{previous['rep']}: hidden "
              f"{updated['hidden_passed']}/{updated['hidden_total']} (was {previous['hidden_passed']})", flush=True)
        all_results.append(updated)
    (args.results_dir / "results.json").write_text(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()
