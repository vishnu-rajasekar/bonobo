import json
from pathlib import Path

from morph_engine.experiments.benchmark_scenarios import get_benchmark_recovery_modes
from morph_engine.experiments.generate_structure import StructureGenerationExperiment


def _mode_record(scenario, result, run_dir):
    summary = result.get("summary", {})
    return {
        "mode": scenario.get("comparison_mode"),
        "label": scenario.get("comparison_label"),
        "scenario_name": scenario.get("scenario_name"),
        "run_dir": str(run_dir),
        "iterations_executed": summary.get("iterations_executed"),
        "rule_sequence": summary.get("rule_sequence"),
        "final_node_count": summary.get("final_node_count"),
        "final_edge_count": summary.get("final_edge_count"),
        "final_residual_magnitude": summary.get("final_residual_magnitude"),
        "global_equilibrium_valid": summary.get("global_equilibrium_valid"),
        "termination_reason": summary.get("termination_reason"),
        "support_distance_history": summary.get("support_distance_history"),
        "support_connectivity_history": summary.get("support_connectivity_history"),
    }


def main():
    repo_root = Path(__file__).resolve().parent.parent
    results = []
    for scenario in get_benchmark_recovery_modes():
        experiment = StructureGenerationExperiment(scenario=scenario)
        _, result, run_dir = experiment.run()
        results.append(_mode_record(scenario, result, run_dir))

    out_path = repo_root / "experiments" / "benchmark_recovery_comparison.json"
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)

    print(json.dumps(results, indent=2))
    print("saved:", out_path)


if __name__ == "__main__":
    main()
