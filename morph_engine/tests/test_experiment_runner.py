import json
from pathlib import Path

from morph_engine.experiments.runner_v1 import ExperimentRunner


def test_experiment_runner_executes():
    base_dir = Path(__file__).resolve().parent.parent.parent
    config_path = base_dir / "experiments" / "configs" / "basic_growth.json"

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    runner = ExperimentRunner(config)
    graph, result = runner.run()

    assert graph is not None
    assert isinstance(result, dict)
    assert "steps_executed" in result
    assert result["steps_executed"] <= config["max_steps"]
    assert "channels" in result
