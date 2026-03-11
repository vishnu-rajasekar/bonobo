import json
from pathlib import Path


def _latest_run_dir(repo_root):
    runs_dir = repo_root / "experiments" / "runs"
    run_dirs = sorted([path for path in runs_dir.iterdir() if path.is_dir()])
    if not run_dirs:
        raise FileNotFoundError("No run directories found in {0}".format(runs_dir))
    return run_dirs[-1]


def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    repo_root = Path(__file__).resolve().parent.parent
    run_dir = _latest_run_dir(repo_root)
    ml_export = _load_json(run_dir / "ml_export.json")

    payload = {
        "run_dir": str(run_dir),
        "summary": _load_json(run_dir / "summary.json"),
        "structural_dna": _load_json(run_dir / "structural_dna.json"),
        "accepted_graph_digest": _load_json(run_dir / "accepted_graph_digest.json"),
        "ml_export_sample": {
            "node_ids": ml_export.get("node_ids", []),
            "node_features": ml_export.get("node_features", [])[:3],
            "edge_index": ml_export.get("edge_index", [])[:5],
            "edge_features": ml_export.get("edge_features", [])[:5],
            "global_features": ml_export.get("global_features", []),
        },
    }

    out_path = repo_root / "experiments" / "last_benchmark_report.json"
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    print(json.dumps(payload, indent=2))
    print("saved_report:", out_path)


if __name__ == "__main__":
    main()
