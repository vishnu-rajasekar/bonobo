import argparse
import json
from pathlib import Path

from morph_engine.experiments.policy_study_v1 import run_policy_baseline_study
from morph_engine.experiments.policy_study_v1 import save_policy_baseline_study


def main():
    parser = argparse.ArgumentParser(description="Run baseline policy comparison study for Bonobo.")
    parser.add_argument("--runs", type=int, default=5, help="Number of seeds/runs per policy.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    payload = run_policy_baseline_study(seeds=list(range(int(args.runs))))
    out_path = save_policy_baseline_study(payload, repo_root / "experiments" / "policy_baseline_comparison.json")

    print(json.dumps(payload, indent=2))
    print("saved:", out_path)


if __name__ == "__main__":
    main()
