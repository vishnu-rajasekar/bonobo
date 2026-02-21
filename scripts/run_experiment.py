import json
import os

from morph_engine.experiments.runner_v1 import ExperimentRunner
from pathlib import Path

def main():
    BASE_DIR = Path(__file__).resolve().parent.parent
    config_path = BASE_DIR / "experiments" / "configs" / "basic_growth.json"

    with open(config_path, "r", encoding="utf-8") as handle:
        config = json.load(handle)

    runner = ExperimentRunner(config)
    _, result = runner.run()

    global_eq = result["channels"].get("global_equilibrium_v1", {})
    residual = global_eq.get("metrics", {}).get("residual_magnitude")

    print("valid:", result.get("valid"))
    print("global_equilibrium_valid:", global_eq.get("valid"))
    print("residual_magnitude:", residual)


if __name__ == "__main__":
    main()
