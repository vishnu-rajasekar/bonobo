import json
from pathlib import Path


def _json_ready(value):
    if hasattr(value, "to_data") and callable(getattr(value, "to_data")):
        return value.to_data()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _to_payload(
    *,
    assembly,
    trace,
    scenario_name,
    seed,
    problem_id=None,
    policy_id=None,
    step_budget=None,
    termination_reason=None,
    final_metrics=None,
):
    return {
        "scenario_name": scenario_name,
        "problem_id": problem_id or scenario_name,
        "policy_id": policy_id or "rule_weighted_random_v1",
        "seed": seed,
        "step_budget": step_budget,
        "termination_reason": termination_reason,
        "assembly": assembly.to_data(),
        "trace": list(trace),
        "final_metrics": final_metrics or {},
    }


def export_run(
    run_dir,
    assembly,
    trace,
    scenario_name,
    seed,
    problem_id=None,
    policy_id=None,
    step_budget=None,
    termination_reason=None,
    final_metrics=None,
):
    run_path = Path(run_dir)
    run_path.mkdir(parents=True, exist_ok=True)
    payload = _to_payload(
        assembly=assembly,
        trace=trace,
        scenario_name=scenario_name,
        seed=seed,
        problem_id=problem_id,
        policy_id=policy_id,
        step_budget=step_budget,
        termination_reason=termination_reason,
        final_metrics=final_metrics,
    )
    (run_path / "kernel_run.json").write_text(json.dumps(payload, indent=2))
    return run_path / "kernel_run.json"


def export_batch_summary(out_path, payload):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(_json_ready(payload), indent=2))
    return out_path
