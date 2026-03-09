import json
from pathlib import Path

from morph_engine.experiments.generate_structure import StructureGenerationExperiment


def _load_iteration_history(run_dir):
    run_path = Path(run_dir)
    trace_path = run_path / "trace.json"
    snapshots_dir = run_path / "snapshots"

    trace = []
    if trace_path.exists():
        with open(trace_path, "r", encoding="utf-8") as handle:
            trace = json.load(handle)
    action_by_step = {int(item.get("step", -1)): item.get("action") for item in trace}

    snapshots = sorted(snapshots_dir.glob("step_*.json"))
    iterations = []
    for snapshot in snapshots:
        stem = snapshot.stem
        step = int(stem.split("_")[1])
        with open(snapshot, "r", encoding="utf-8") as handle:
            graph_state = json.load(handle)

        iterations.append(
            {
                "step": step,
                "rule": action_by_step.get(step),
                "graph": graph_state,
            }
        )
    return iterations


def main():
    base_dir = Path(__file__).resolve().parent.parent
    config_path = base_dir / "experiments" / "configs" / "basic_growth.json"

    with open(config_path, "r", encoding="utf-8") as handle:
        config = json.load(handle)

    iterations = int(config.get("iterations", config.get("max_steps", 20)))
    seed = int(config.get("seed", 0))
    experiment = StructureGenerationExperiment(iterations=iterations, seed=seed)
    _, result, run_dir = experiment.run()

    history = _load_iteration_history(run_dir)
    payload = {
        "run_dir": str(run_dir),
        "iterations": history,
        "metrics": result,
    }

    out_path = base_dir / "experiments" / "last_run.json"
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    global_eq = result.get("channels", {}).get("global_equilibrium_v1", {})
    residual = global_eq.get("metrics", {}).get("residual_magnitude")

    print("saved:", out_path)
    print("iterations:", len(history))
    print("valid:", result.get("valid"))
    print("global_equilibrium_valid:", global_eq.get("valid"))
    print("residual_magnitude:", residual)


if __name__ == "__main__":
    main()
