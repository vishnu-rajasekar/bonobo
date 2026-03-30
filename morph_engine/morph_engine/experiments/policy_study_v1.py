import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

from morph_engine.experiments.benchmark_scenarios import get_benchmark_scenario
from morph_engine.experiments.generate_structure import StructureGenerationExperiment
from morph_engine.experiments.logger_v1 import ExperimentLogger


DEFAULT_POLICY_STUDY_POLICIES = [
    {
        "policy_name": "benchmark_ranked",
        "policy_settings": {},
        "label": "default_benchmark_policy",
    },
    {
        "policy_name": "heuristic",
        "policy_settings": {},
        "label": "heuristic_policy",
    },
    {
        "policy_name": "random",
        "policy_settings": {},
        "label": "random_policy",
    },
    {
        "policy_name": "weighted_random",
        "policy_settings": {
            "rule_weights": {
                "extend_node": 1.5,
                "split_node": 1.0,
                "connect_two_nodes": 1.2,
                "extend_and_connect_two_nodes": 1.2,
                "close_structure": 1.1,
            },
            "operator_weights": {
                "vector_loa_extension": 1.4,
                "direct_two_force_connection": 1.1,
                "triangle_closure_strategy": 1.05,
            },
        },
        "label": "weighted_random_policy",
    },
]


def _support_path(graph):
    load_nodes = sorted({str(load.get("node")) for load in graph.get_loads() if load.get("node") is not None})
    support_nodes = []
    for node_key in graph.network.nodes():
        fixed = graph.network.node_attribute(node_key, "fixed") or [0, 0, 0]
        if any(float(value) != 0.0 for value in fixed):
            support_nodes.append(str(node_key))

    if not load_nodes or not support_nodes:
        return None

    adjacency = {}
    for node_key in graph.network.nodes():
        adjacency[str(node_key)] = set()
    for u, v in graph.network.edges():
        su = str(u)
        sv = str(v)
        adjacency[su].add(sv)
        adjacency[sv].add(su)

    queue = [(load, [load]) for load in load_nodes]
    seen = set(load_nodes)
    support_set = set(support_nodes)
    while queue:
        current, path = queue.pop(0)
        if current in support_set:
            return path
        for neighbor in sorted(adjacency[current]):
            if neighbor in seen:
                continue
            seen.add(neighbor)
            queue.append((neighbor, path + [neighbor]))
    return None


def _count_invalid_joint_rejections(trace):
    count = 0
    for step in trace or []:
        for item in step.get("candidate_evaluations", []):
            if "local_joint_non_equilibrated" in item.get("reason_codes", []):
                count += 1
    return count


def _selected_rule_diversity(summary):
    return len(set(summary.get("rule_sequence", []) or []))


def _record_run(policy_spec, seed, graph, result, run_dir):
    summary = result.get("summary", {})
    trace = result.get("trace", [])
    support_path = _support_path(graph)
    support_distance_history = summary.get("support_distance_history", []) or []
    residual_history = summary.get("residual_history", []) or []
    unresolved_force_magnitude_history = summary.get("unresolved_force_magnitude_history", []) or []
    absorbed_magnitude_history = summary.get("absorbed_magnitude_history", []) or []
    support_distance_delta = None
    if len(support_distance_history) >= 2 and support_distance_history[0] is not None and support_distance_history[-1] is not None:
        support_distance_delta = float(support_distance_history[0]) - float(support_distance_history[-1])
    residual_improved = any(
        float(after) < float(before) - 1e-9 for before, after in zip(residual_history, residual_history[1:])
    )
    unresolved_force_improved = any(
        float(after) < float(before) - 1e-9
        for before, after in zip(unresolved_force_magnitude_history, unresolved_force_magnitude_history[1:])
    )

    return {
        "policy_name": policy_spec["policy_name"],
        "policy_label": policy_spec.get("label", policy_spec["policy_name"]),
        "seed": int(seed),
        "run_dir": str(run_dir),
        "scenario_name": summary.get("scenario_name"),
        "accepted_steps": int(summary.get("iterations_executed", 0)),
        "equilibrium_reached": bool(summary.get("global_equilibrium_valid", False)),
        "termination_reason": summary.get("termination_reason"),
        "final_node_count": int(summary.get("final_node_count", 0)),
        "final_edge_count": int(summary.get("final_edge_count", 0)),
        "final_residual_magnitude": float(summary.get("final_residual_magnitude", 0.0)),
        "final_unresolved_force_magnitude": float(summary.get("final_unresolved_force_magnitude", 0.0)),
        "support_path_exists": support_path is not None,
        "support_path": support_path,
        "plausibility_pass": int(summary.get("two_member_non_collinear_joint_count", 0)) == 0,
        "invalid_joint_rejection_count": _count_invalid_joint_rejections(trace),
        "rule_sequence": list(summary.get("rule_sequence", []) or []),
        "unique_rule_count": _selected_rule_diversity(summary),
        "support_distance_delta": support_distance_delta,
        "residual_improved": residual_improved,
        "unresolved_force_improved": unresolved_force_improved,
        "residual_history": residual_history,
        "unresolved_force_magnitude_history": unresolved_force_magnitude_history,
        "absorbed_magnitude_history": absorbed_magnitude_history,
        "support_trend": dict(summary.get("support_trend", {}) or {}),
    }


def _mean(values):
    if not values:
        return 0.0
    return sum(values) / float(len(values))


def aggregate_policy_metrics(records):
    termination_counter = Counter(record["termination_reason"] for record in records)
    unique_rules = sorted({rule for record in records for rule in record.get("rule_sequence", [])})
    support_distance_deltas = [value for value in (record.get("support_distance_delta") for record in records) if value is not None]

    return {
        "run_count": len(records),
        "accepted_step_count": {
            "min": min(record["accepted_steps"] for record in records) if records else 0,
            "max": max(record["accepted_steps"] for record in records) if records else 0,
            "mean": _mean([record["accepted_steps"] for record in records]),
        },
        "equilibrium_count": sum(1 for record in records if record["equilibrium_reached"]),
        "support_path_exists_count": sum(1 for record in records if record["support_path_exists"]),
        "plausibility_pass_count": sum(1 for record in records if record["plausibility_pass"]),
        "termination_reason_distribution": dict(termination_counter),
        "invalid_joint_rejection": {
            "runs_with_invalid_joint_rejection": sum(1 for record in records if record["invalid_joint_rejection_count"] > 0),
            "total_count": sum(record["invalid_joint_rejection_count"] for record in records),
            "mean_per_run": _mean([record["invalid_joint_rejection_count"] for record in records]),
        },
        "action_rule_diversity": {
            "unique_rules_observed": unique_rules,
            "mean_unique_rules_per_run": _mean([record["unique_rule_count"] for record in records]),
        },
        "mean_final_node_count": _mean([record["final_node_count"] for record in records]),
        "mean_final_edge_count": _mean([record["final_edge_count"] for record in records]),
        "mean_final_residual_magnitude": _mean([record["final_residual_magnitude"] for record in records]),
        "mean_final_unresolved_force_magnitude": _mean([record["final_unresolved_force_magnitude"] for record in records]),
        "runs_with_residual_improvement": sum(1 for record in records if record["residual_improved"]),
        "runs_with_unresolved_force_improvement": sum(1 for record in records if record["unresolved_force_improved"]),
        "support_engagement": {
            "mean_support_distance_delta": _mean(support_distance_deltas),
            "mean_steps_closer_to_support": _mean(
                [record.get("support_trend", {}).get("accepted_steps_closer_to_support", 0) for record in records]
            ),
            "mean_steps_improved_support_connectivity": _mean(
                [record.get("support_trend", {}).get("accepted_steps_improved_support_connectivity", 0) for record in records]
            ),
        },
    }


def choose_representative_runs(records):
    if not records:
        return {"best": None, "median": None, "failed": None}

    def _rank_best(record):
        return (
            1 if record["plausibility_pass"] else 0,
            1 if record["support_path_exists"] else 0,
            1 if record["equilibrium_reached"] else 0,
            record["accepted_steps"],
            -record["final_residual_magnitude"],
        )

    sorted_best = sorted(records, key=_rank_best, reverse=True)
    best = sorted_best[0]

    sorted_by_steps = sorted(records, key=lambda record: (record["accepted_steps"], record["seed"]))
    median = sorted_by_steps[len(sorted_by_steps) // 2]

    failed_candidates = [record for record in records if not record["equilibrium_reached"]]
    if not failed_candidates:
        failed = sorted_by_steps[0]
    else:
        common_reason = Counter(record["termination_reason"] for record in failed_candidates).most_common(1)[0][0]
        same_reason = [record for record in failed_candidates if record["termination_reason"] == common_reason]
        failed = sorted(same_reason, key=lambda record: (record["accepted_steps"], record["final_residual_magnitude"], record["seed"]))[0]

    def _compact(record):
        if record is None:
            return None
        return {
            "seed": record["seed"],
            "run_dir": record["run_dir"],
            "accepted_steps": record["accepted_steps"],
            "termination_reason": record["termination_reason"],
            "equilibrium_reached": record["equilibrium_reached"],
            "support_path_exists": record["support_path_exists"],
            "plausibility_pass": record["plausibility_pass"],
        }

    return {
        "best": _compact(best),
        "median": _compact(median),
        "failed": _compact(failed),
    }


def run_policy_baseline_study(
    *,
    seeds=None,
    policies=None,
    base_scenario_name="mitchell_planar_benchmark_v1",
    base_logger_path=None,
):
    seeds = list(range(5)) if seeds is None else [int(seed) for seed in seeds]
    policies = deepcopy(DEFAULT_POLICY_STUDY_POLICIES if policies is None else policies)

    per_policy = []
    for policy_spec in policies:
        records = []
        for seed in seeds:
            scenario = get_benchmark_scenario(base_scenario_name)
            scenario["seed"] = int(seed)
            scenario["policy_name"] = policy_spec["policy_name"]
            scenario["selection_policy"] = policy_spec["policy_name"]
            scenario["policy_settings"] = dict(policy_spec.get("policy_settings", {}))

            experiment = StructureGenerationExperiment(
                scenario=scenario,
                logger=None if base_logger_path is None else ExperimentLogger(base_path=base_logger_path),
            )
            graph, result, run_dir = experiment.run()
            records.append(_record_run(policy_spec, seed, graph, result, run_dir))

        per_policy.append(
            {
                "policy_name": policy_spec["policy_name"],
                "policy_label": policy_spec.get("label", policy_spec["policy_name"]),
                "policy_settings": dict(policy_spec.get("policy_settings", {})),
                "aggregate_metrics": aggregate_policy_metrics(records),
                "representative_runs": choose_representative_runs(records),
                "runs": records,
            }
        )

    return {
        "study_name": "policy_baseline_study_v1",
        "scenario_name": base_scenario_name,
        "seed_count": len(seeds),
        "seeds": seeds,
        "policies_compared": [item["policy_name"] for item in per_policy],
        "per_policy": per_policy,
    }


def save_policy_baseline_study(payload, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return out_path
