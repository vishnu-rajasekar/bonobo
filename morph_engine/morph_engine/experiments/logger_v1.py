import json
import os
from datetime import datetime


class ExperimentLogger:
    def __init__(self, base_path="experiments/runs"):
        self.base_path = base_path
        self.run_dir = None

    def create_run_dir(self):
        if self.run_dir is not None:
            return self.run_dir

        os.makedirs(self.base_path, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.join(self.base_path, stamp)
        suffix = 1
        while os.path.exists(run_dir):
            run_dir = os.path.join(self.base_path, "{0}_{1}".format(stamp, suffix))
            suffix += 1

        os.makedirs(run_dir, exist_ok=True)
        self.run_dir = run_dir
        return self.run_dir

    def _write_json(self, filename, data):
        run_dir = self.create_run_dir()
        path = os.path.join(run_dir, filename)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        return path

    def save_json(self, filename, data):
        return self._write_json(filename, data)

    def artifact_path(self, filename):
        run_dir = self.create_run_dir()
        return os.path.join(run_dir, filename)

    def save_config(self, config):
        return self._write_json("config.json", config)

    def save_graph(self, graph):
        return self._write_json("final_graph.json", graph.to_json())

    def save_trace(self, trace):
        return self._write_json("trace.json", trace)

    def save_metrics(self, metrics):
        return self._write_json("metrics.json", metrics)
