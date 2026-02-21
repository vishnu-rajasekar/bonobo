import json
import os
import tempfile

from morph_engine.experiments.logger_v1 import ExperimentLogger
from morph_engine.model.structural_graph import StructuralGraph


def test_experiment_logger_creates_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ExperimentLogger(base_path=tmpdir)

        config = {"max_steps": 5, "seed": 1}
        graph = StructuralGraph()
        trace = [{"step": 0, "action": "dummy"}]
        metrics = {"valid": False}

        logger.create_run_dir()
        logger.save_config(config)
        logger.save_graph(graph)
        logger.save_trace(trace)
        logger.save_metrics(metrics)

        run_dirs = os.listdir(tmpdir)
        assert len(run_dirs) == 1

        run_path = os.path.join(tmpdir, run_dirs[0])
        expected_files = {
            "config.json",
            "final_graph.json",
            "trace.json",
            "metrics.json",
        }

        assert expected_files.issubset(set(os.listdir(run_path)))

        with open(os.path.join(run_path, "config.json"), encoding="utf-8") as f:
            loaded = json.load(f)
            assert loaded["seed"] == 1
