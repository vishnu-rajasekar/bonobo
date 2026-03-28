import json
from pathlib import Path

from morph_engine.experiments.benchmark_scenarios import get_benchmark_scenario
from morph_engine.experiments.generate_structure import StructureGenerationExperiment


def main():
    base_dir = Path(__file__).resolve().parent.parent
    scenario = get_benchmark_scenario()
    experiment = StructureGenerationExperiment(scenario=scenario)
    _, result, run_dir = experiment.run()

    payload = {
        "run_dir": str(run_dir),
        "summary": result.get("summary", {}),
        "structural_dna": result.get("structural_dna", {}),
        "trace_excerpt": result.get("trace_excerpt", []),
        "accepted_graph_digest": result.get("accepted_graph_digest", {}),
        "ml_export_sample": {
            "node_ids": result.get("ml_export", {}).get("node_ids", []),
            "node_features": result.get("ml_export", {}).get("node_features", [])[:3],
            "edge_index": result.get("ml_export", {}).get("edge_index", [])[:5],
            "edge_features": result.get("ml_export", {}).get("edge_features", [])[:5],
            "global_features": result.get("ml_export", {}).get("global_features", []),
        },
    }

    out_path = base_dir / "experiments" / "last_run.json"
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    summary = result.get("summary", {})
    print("saved:", out_path)
    print("run_dir:", run_dir)
    print("scenario_name:", summary.get("scenario_name"))
    print("iterations_executed:", summary.get("iterations_executed"))
    print("final_residual_magnitude:", summary.get("final_residual_magnitude"))
    print("global_equilibrium_valid:", summary.get("global_equilibrium_valid"))


if __name__ == "__main__":
    main()
