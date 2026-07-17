import argparse
import sys
from datetime import datetime
from datetime import timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "morph_engine"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from morph_engine.vector_gs_kernel_v1.export import export_run
from morph_engine.vector_gs_kernel_v1.export import export_batch_summary
from morph_engine.vector_gs_kernel_v1.experiments import DEFAULT_POLICY_ID
from morph_engine.vector_gs_kernel_v1.experiments import run_kernel_batch


def main():
    parser = argparse.ArgumentParser(description="Run the standalone vector graphic statics kernel.")
    parser.add_argument("--runs", type=int, default=3, help="Number of seeded episodes to run.")
    parser.add_argument("--steps", type=int, default=12, help="Maximum steps per episode.")
    parser.add_argument(
        "--growth-limit",
        type=int,
        default=None,
        help="Accepted growth-rule count before the deterministic closure phase.",
    )
    parser.add_argument("--policy-id", default=DEFAULT_POLICY_ID, help="Policy label recorded in kernel artifacts.")
    parser.add_argument("--problem-id", default=None, help="Problem id recorded in kernel artifacts.")
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "experiments" / "vector_gs_kernel_v1_runs"),
        help="Directory for saved kernel runs.",
    )
    args = parser.parse_args()

    base_dir = Path(args.output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    batch_stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    payload = run_kernel_batch(
        seeds=list(range(int(args.runs))),
        max_steps=int(args.steps),
        problem_id=args.problem_id,
        policy_id=args.policy_id,
        growth_limit=args.growth_limit,
    )

    for record in payload["runs"]:
        run_dir = base_dir / f"{batch_stamp}_seed_{record['seed']}"
        artifact = export_run(
            run_dir,
            record["assembly"],
            record["trace"],
            record["scenario_name"],
            record["seed"],
            problem_id=record["problem_id"],
            policy_id=record["policy_id"],
            step_budget=record["step_budget"],
            termination_reason=record["termination_reason"],
            final_metrics=record["final_metrics"],
        )
        print(
            {
                "seed": record["seed"],
                "artifact": str(artifact),
                "problem_id": record["problem_id"],
                "policy_id": record["policy_id"],
                "state": record["assembly"].state,
                "node_count": len(record["assembly"].nodes),
                "member_count": len(record["assembly"].members),
                "residual_magnitude": record["final_metrics"]["final_residual_magnitude"],
                "rule_sequence": [step["rule"] for step in record["trace"]],
                "final_phase": record["final_phase"],
                "termination_reason": record["termination_reason"],
                "growth_step_count": record["growth_step_count"],
                "closure_step_count": record["closure_step_count"],
            }
        )

    summary_path = export_batch_summary(base_dir / f"{batch_stamp}_batch_summary.json", payload)
    print({"batch_summary": str(summary_path), "aggregate_metrics": payload["aggregate_metrics"]})


if __name__ == "__main__":
    raise SystemExit(main())
