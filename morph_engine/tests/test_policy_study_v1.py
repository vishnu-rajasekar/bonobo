import tempfile

from morph_engine.experiments.policy_study_v1 import aggregate_policy_metrics
from morph_engine.experiments.policy_study_v1 import choose_representative_runs
from morph_engine.experiments.policy_study_v1 import run_policy_baseline_study


def test_aggregate_policy_metrics_structure():
    records = [
        {
            "accepted_steps": 1,
            "equilibrium_reached": False,
            "support_path_exists": False,
            "plausibility_pass": True,
            "termination_reason": "no_admissible_candidate",
            "invalid_joint_rejection_count": 2,
            "rule_sequence": ["extend_node_rule"],
            "unique_rule_count": 1,
            "final_node_count": 4,
            "final_edge_count": 1,
            "final_residual_magnitude": 10.0,
            "final_unresolved_force_magnitude": 10.0,
            "residual_improved": False,
            "unresolved_force_improved": False,
            "support_distance_delta": 0.2,
            "support_trend": {
                "accepted_steps_closer_to_support": 1,
                "accepted_steps_improved_support_connectivity": 0,
            },
        },
        {
            "accepted_steps": 2,
            "equilibrium_reached": True,
            "support_path_exists": True,
            "plausibility_pass": True,
            "termination_reason": "equilibrium_reached",
            "invalid_joint_rejection_count": 0,
            "rule_sequence": ["extend_node_rule", "triangle_closure_rule"],
            "unique_rule_count": 2,
            "final_node_count": 5,
            "final_edge_count": 2,
            "final_residual_magnitude": 0.0,
            "final_unresolved_force_magnitude": 0.0,
            "residual_improved": True,
            "unresolved_force_improved": True,
            "support_distance_delta": 0.8,
            "support_trend": {
                "accepted_steps_closer_to_support": 2,
                "accepted_steps_improved_support_connectivity": 1,
            },
        },
    ]

    metrics = aggregate_policy_metrics(records)

    assert metrics["run_count"] == 2
    assert metrics["accepted_step_count"]["max"] == 2
    assert metrics["equilibrium_count"] == 1
    assert metrics["support_path_exists_count"] == 1
    assert metrics["plausibility_pass_count"] == 2
    assert "equilibrium_reached" in metrics["termination_reason_distribution"]
    assert metrics["invalid_joint_rejection"]["total_count"] == 2
    assert "triangle_closure_rule" in metrics["action_rule_diversity"]["unique_rules_observed"]
    assert "mean_final_unresolved_force_magnitude" in metrics
    assert "runs_with_residual_improvement" in metrics
    assert "runs_with_unresolved_force_improvement" in metrics


def test_choose_representative_runs_picks_best_median_failed():
    records = [
        {
            "seed": 0,
            "run_dir": "run_a",
            "accepted_steps": 1,
            "termination_reason": "no_admissible_candidate",
            "equilibrium_reached": False,
            "support_path_exists": False,
            "plausibility_pass": True,
            "final_residual_magnitude": 10.0,
        },
        {
            "seed": 1,
            "run_dir": "run_b",
            "accepted_steps": 3,
            "termination_reason": "equilibrium_reached",
            "equilibrium_reached": True,
            "support_path_exists": True,
            "plausibility_pass": True,
            "final_residual_magnitude": 0.0,
        },
        {
            "seed": 2,
            "run_dir": "run_c",
            "accepted_steps": 2,
            "termination_reason": "no_admissible_candidate",
            "equilibrium_reached": False,
            "support_path_exists": True,
            "plausibility_pass": False,
            "final_residual_magnitude": 5.0,
        },
    ]

    representatives = choose_representative_runs(records)

    assert representatives["best"]["run_dir"] == "run_b"
    assert representatives["median"]["run_dir"] == "run_c"
    assert representatives["failed"]["termination_reason"] == "no_admissible_candidate"


def test_policy_study_runner_output_structure():
    with tempfile.TemporaryDirectory() as tmpdir:
        payload = run_policy_baseline_study(seeds=[0], base_logger_path=tmpdir)

    assert payload["study_name"] == "policy_baseline_study_v1"
    assert payload["seed_count"] == 1
    assert "benchmark_ranked" in payload["policies_compared"]
    assert len(payload["per_policy"]) >= 3
    first_policy = payload["per_policy"][0]
    assert "aggregate_metrics" in first_policy
    assert "representative_runs" in first_policy
    assert "runs" in first_policy
