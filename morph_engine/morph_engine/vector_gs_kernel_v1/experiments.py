from copy import deepcopy
from collections import Counter

from .engine import GDGS_NODE_RULE_UNIFORM_POLICY_ID
from .engine import VectorGSKernelV1
from .metrics import compute_kernel_metrics
from .scenarios import make_default_cantilever_scenario


DEFAULT_POLICY_ID = GDGS_NODE_RULE_UNIFORM_POLICY_ID


def run_kernel_episode(
    *,
    seed,
    max_steps=12,
    scenario_builder=None,
    problem_id=None,
    policy_id=DEFAULT_POLICY_ID,
    growth_limit=None,
    rule_parameter_configuration=None,
):
    scenario_builder = scenario_builder or make_default_cantilever_scenario
    assembly = scenario_builder()
    scenario_name = assembly.metadata.get("scenario_name", "kernel_scenario")
    resolved_problem_id = problem_id or scenario_name

    kernel = VectorGSKernelV1(
        seed=int(seed),
        policy_id=policy_id,
        growth_limit=growth_limit,
        rule_parameter_configuration=rule_parameter_configuration,
    )
    final_assembly, trace = kernel.run(assembly, max_steps=int(max_steps))
    final_metrics = compute_kernel_metrics(final_assembly, trace=trace)

    return {
        "problem_id": resolved_problem_id,
        "policy_id": policy_id,
        "scenario_name": scenario_name,
        "seed": int(seed),
        "step_budget": int(max_steps),
        "growth_limit": kernel.growth_limit,
        "reaction_angle_configuration": deepcopy(
            final_assembly.metadata.get("reaction_angle_configuration")
        ),
        "rule_parameter_configuration": deepcopy(
            final_assembly.metadata.get("rule_parameter_configuration")
        ),
        "growth_step_count": final_assembly.metadata.get("growth_step_count", 0),
        "closure_step_count": final_assembly.metadata.get("closure_step_count", 0),
        "closure_started_at_step": final_assembly.metadata.get("closure_started_at_step"),
        "final_phase": final_assembly.metadata.get("final_phase", final_assembly.state),
        "termination_reason": final_assembly.metadata.get("termination_reason"),
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
            "termination_reason_counts": {},
            "mean_growth_steps": 0.0,
            "mean_closure_steps": 0.0,
            "closure_start_step_distribution": {},
            "phase_transition_counts": {},
            "member_force_classification_valid_run_count": 0,
            "total_tension_member_count": 0,
            "total_compression_member_count": 0,
            "total_unknown_member_count": 0,
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
    member_force_diagnostics = [
        record["final_metrics"].get("member_force_diagnostics", {}) for record in records
    ]
    invalidity_reason_counts = Counter()
    termination_reason_counts = Counter(record.get("termination_reason") or "unknown" for record in records)
    closure_start_step_distribution = Counter(
        str(record["closure_started_at_step"])
        for record in records
        if record.get("closure_started_at_step") is not None
    )
    phase_transition_counts = Counter(
        "{0}->{1}".format(step["phase_before"], step["phase_after"])
        for record in records
        for step in record["trace"]
        if step["phase_before"] != step["phase_after"]
    )
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
        "termination_reason_counts": dict(sorted(termination_reason_counts.items())),
        "mean_growth_steps": sum(record["growth_step_count"] for record in records) / float(run_count),
        "mean_closure_steps": sum(record["closure_step_count"] for record in records) / float(run_count),
        "closure_start_step_distribution": dict(sorted(closure_start_step_distribution.items())),
        "phase_transition_counts": dict(sorted(phase_transition_counts.items())),
        "member_force_classification_valid_run_count": sum(
            1 for diagnostic in member_force_diagnostics if diagnostic.get("all_classifications_valid")
        ),
        "total_tension_member_count": sum(
            diagnostic.get("tension_count", 0) for diagnostic in member_force_diagnostics
        ),
        "total_compression_member_count": sum(
            diagnostic.get("compression_count", 0) for diagnostic in member_force_diagnostics
        ),
        "total_unknown_member_count": sum(
            diagnostic.get("unknown_count", 0) for diagnostic in member_force_diagnostics
        ),
    }


def run_kernel_batch(
    *,
    seeds,
    max_steps=12,
    scenario_builder=None,
    problem_id=None,
    policy_id=DEFAULT_POLICY_ID,
    growth_limit=None,
    rule_parameter_configuration=None,
):
    records = [
        run_kernel_episode(
            seed=seed,
            max_steps=max_steps,
            scenario_builder=scenario_builder,
            problem_id=problem_id,
            policy_id=policy_id,
            growth_limit=growth_limit,
            rule_parameter_configuration=rule_parameter_configuration,
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
        "growth_limit": records[0]["growth_limit"] if records else growth_limit,
        "reaction_angle_configuration": (
            records[0]["reaction_angle_configuration"] if records else None
        ),
        "rule_parameter_configuration": (
            records[0]["rule_parameter_configuration"] if records else None
        ),
        "runs": records,
        "aggregate_metrics": _aggregate_batch_metrics(records),
    }
