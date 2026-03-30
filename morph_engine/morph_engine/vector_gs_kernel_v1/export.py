import json
from pathlib import Path


def export_run(run_dir, assembly, trace, scenario_name, seed):
    run_path = Path(run_dir)
    run_path.mkdir(parents=True, exist_ok=True)
    payload = {
        "scenario_name": scenario_name,
        "seed": seed,
        "assembly": assembly.to_data(),
        "trace": list(trace),
    }
    (run_path / "kernel_run.json").write_text(json.dumps(payload, indent=2))
    return run_path / "kernel_run.json"

