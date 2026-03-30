import argparse
import sys
from datetime import datetime
from datetime import timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "morph_engine"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from morph_engine.vector_gs_kernel_v1 import VectorGSKernelV1
from morph_engine.vector_gs_kernel_v1.export import export_run
from morph_engine.vector_gs_kernel_v1.scenarios import make_default_cantilever_scenario


def main():
    parser = argparse.ArgumentParser(description="Run the standalone vector graphic statics kernel.")
    parser.add_argument("--runs", type=int, default=3, help="Number of seeded episodes to run.")
    parser.add_argument("--steps", type=int, default=12, help="Maximum steps per episode.")
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "experiments" / "vector_gs_kernel_v1_runs"),
        help="Directory for saved kernel runs.",
    )
    args = parser.parse_args()

    base_dir = Path(args.output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    for seed in range(int(args.runs)):
        assembly = make_default_cantilever_scenario()
        kernel = VectorGSKernelV1(seed=seed)
        final_assembly, trace = kernel.run(assembly, max_steps=int(args.steps))
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_dir = base_dir / f"{stamp}_seed_{seed}"
        artifact = export_run(run_dir, final_assembly, trace, final_assembly.metadata.get("scenario_name", "kernel_scenario"), seed)
        print(
            {
                "seed": seed,
                "artifact": str(artifact),
                "state": final_assembly.state,
                "node_count": len(final_assembly.nodes),
                "member_count": len(final_assembly.members),
                "residual_magnitude": final_assembly.residual_magnitude(),
                "rule_sequence": [step["rule"] for step in trace],
            }
        )


if __name__ == "__main__":
    raise SystemExit(main())
