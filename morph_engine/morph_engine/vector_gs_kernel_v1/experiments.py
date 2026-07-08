from copy import deepcopy
from collections import Counter

from .engine import VectorGSKernelV1
from .metrics import compute_kernel_metrics
from .scenarios import make_default_cantilever_scenario


DEFAULT_POLICY_ID = "rule_weighted_random_v1"


def run_kernel_episode(
    *,
    seed,
    max_steps=12,
    scenario_builder=None,
    problem_id=None,
    policy_id=DEFAULT_POLICY_ID,
):
    scenario_builder = scenario_builder or make_default_cantilever_scenario
    assembly = scenario_builder()
    scenario_name = assembly.metadata.get("scenario_name", "kernel_scenario")
    resolved_problem_id = problem_id or scenario_name

    kernel = VectorGSKernelV1(seed=int(seed), policy_id=policy_id)
    final_assembly, trace = kernel.run(assembly, max_steps=int(max_steps))
    final_metrics = compute_kernel_metrics(final_assembly, trace=trace)

    return {
        "problem_id": resolved_problem_id,
        "policy_id": policy_id,
        "scenario_name": scenario_name,
        "seed": int(seed),
        "step_budget": int(max_steps),
        "assembly": deepcopy(final_assembly),
        "trace": list(trace),
        "final_metrics": final_metrics,
    }


def _aggregate_batch_metrics(records):
    if not records:
        return {
            "run_count": 0,
            "completion_rate": 0.0,
            "benchmark_completion_rate": 0.0,
            "mean_accepted_steps": 0.0,
            "mean_final_residual_magnitude": 0.0,
            "mean_material_proxy_total_member_length": 0.0,
            "support_connected_run_count": 0,
            "geometrically_valid_run_count": 0,
            "benchmark_complete_run_count": 0,
            "invalidity_reason_counts": {},
        }

    run_count = len(records)
    completed = sum(1 for record in records if record["final_metrics"]["equilibrium_reached"])
    benchmark_completed = sum(1 for record in records if record["final_metrics"].get("benchmark_complete"))
    support_connected = sum(
        1 for record in records if record["final_metrics"]["support_connectivity"]["support_connected"]
    )
    geometrically_valid = sum(
        1
        for record in records
        if record["final_metrics"].get("benchmark_validity", {}).get("geometrically_valid")
    )
    invalidity_reason_counts = Counter()
    for record in records:
        invalidity_reason_counts.update(
            record["final_metrics"].get("benchmark_validity", {}).get("invalid_reasons", [])
        )
    return {
        "run_count": run_count,
        "completion_rate": completed / float(run_count),
        "benchmark_completion_rate": benchmark_completed / float(run_count),
        "mean_accepted_steps": sum(record["final_metrics"]["accepted_step_count"] for record in records) / float(run_count),
        "mean_final_residual_magnitude": sum(
            record["final_metrics"]["final_residual_magnitude"] for record in records
        )
        / float(run_count),
        "mean_material_proxy_total_member_length": sum(
            record["final_metrics"]["material_proxy_total_member_length"] for record in records
        )
        / float(run_count),
        "support_connected_run_count": support_connected,
        "geometrically_valid_run_count": geometrically_valid,
        "benchmark_complete_run_count": benchmark_completed,
        "invalidity_reason_counts": dict(sorted(invalidity_reason_counts.items())),
    }


def run_kernel_batch(
    *,
    seeds,
    max_steps=12,
    scenario_builder=None,
    problem_id=None,
    policy_id=DEFAULT_POLICY_ID,
):
    records = [
        run_kernel_episode(
            seed=seed,
            max_steps=max_steps,
            scenario_builder=scenario_builder,
            problem_id=problem_id,
            policy_id=policy_id,
        )
        for seed in list(seeds)
    ]
    return {
        "study_name": "vector_gs_kernel_batch_v1",
        "problem_id": records[0]["problem_id"] if records else (problem_id or "kernel_problem"),
        "policy_id": policy_id,
        "seeds": [record["seed"] for record in records],
        "seed_count": len(records),
        "step_budget": int(max_steps),
        "runs": records,
        "aggregate_metrics": _aggregate_batch_metrics(records),
    }
