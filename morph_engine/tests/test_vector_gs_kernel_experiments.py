import json
import runpy
import sys
from pathlib import Path

import pytest

import morph_engine.vector_gs_kernel_v1.experiments as kernel_experiments
from morph_engine.vector_gs_kernel_v1.experiments import run_kernel_batch
from morph_engine.vector_gs_kernel_v1.experiments import run_kernel_episode
from morph_engine.vector_gs_kernel_v1.export import export_batch_summary
from morph_engine.vector_gs_kernel_v1.export import export_run
from morph_engine.vector_gs_kernel_v1.scenarios import make_michell_diversity_cantilever_scenario


def test_run_kernel_episode_is_reproducible_for_same_seed():
    episode_a = run_kernel_episode(seed=0, max_steps=8)
    episode_b = run_kernel_episode(seed=0, max_steps=8)

    assert episode_a["problem_id"] == episode_b["problem_id"]
    assert episode_a["policy_id"] == episode_b["policy_id"]
    assert episode_a["trace"] == episode_b["trace"]
    assert episode_a["final_metrics"] == episode_b["final_metrics"]
    assert episode_a["assembly"].to_data() == episode_b["assembly"].to_data()
    assert episode_a["termination_reason"] == episode_b["termination_reason"]


def test_export_run_writes_enriched_kernel_payload(tmp_path):
    episode = run_kernel_episode(
        seed=1,
        max_steps=8,
        problem_id="paper_case_v1",
        policy_id="rule_uniform_random_v1",
    )
    out_path = export_run(
        tmp_path / "seed_1",
        episode["assembly"],
        episode["trace"],
        episode["scenario_name"],
        episode["seed"],
        problem_id=episode["problem_id"],
        policy_id=episode["policy_id"],
        final_metrics=episode["final_metrics"],
    )

    payload = json.loads(out_path.read_text())
    assert payload["seed"] == 1
    assert payload["problem_id"] == "paper_case_v1"
    assert payload["policy_id"] == "rule_uniform_random_v1"
    assert "final_metrics" in payload
    assert "accepted_step_count" in payload["final_metrics"]
    assert "support_connectivity" in payload["final_metrics"]
    assert "boundary_force_polygon" in payload["final_metrics"]
    assert payload["final_metrics"]["boundary_force_polygon"]["externally_balanced"] is True


def test_run_kernel_batch_and_summary_shape(tmp_path):
    payload = run_kernel_batch(seeds=[0, 1], max_steps=8, problem_id="kernel_case_v1", policy_id="rule_weighted_random_v1")
    out_path = export_batch_summary(tmp_path / "batch_summary.json", payload)
    exported = json.loads(out_path.read_text())

    assert exported["study_name"] == "vector_gs_kernel_batch_v1"
    assert exported["problem_id"] == "kernel_case_v1"
    assert exported["policy_id"] == "rule_weighted_random_v1"
    assert exported["seeds"] == [0, 1]
    assert exported["seed_count"] == 2
    assert exported["step_budget"] == 8
    assert len(exported["runs"]) == 2
    assert all(record["step_budget"] == 8 for record in exported["runs"])
    assert "aggregate_metrics" in exported
    assert "completion_rate" in exported["aggregate_metrics"]
    assert "benchmark_completion_rate" in exported["aggregate_metrics"]
    assert "benchmark_complete_run_count" in exported["aggregate_metrics"]
    assert "support_connected_run_count" in exported["aggregate_metrics"]
    assert "geometrically_valid_run_count" in exported["aggregate_metrics"]
    assert "invalidity_reason_counts" in exported["aggregate_metrics"]
    assert "termination_reason_counts" in exported["aggregate_metrics"]


def test_kernel_cli_exports_step_budget_to_run_and_batch_artifacts(tmp_path, monkeypatch):
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "run_vector_gs_kernel_v1.py"
    module = runpy.run_path(str(script_path), run_name="vector_gs_kernel_cli_test")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(script_path),
            "--runs",
            "1",
            "--steps",
            "3",
            "--policy-id",
            "rule_uniform_random_v1",
            "--output-dir",
            str(tmp_path),
        ],
    )

    module["main"]()

    run_path = next(tmp_path.glob("*_seed_0/kernel_run.json"))
    summary_path = next(tmp_path.glob("*_batch_summary.json"))
    assert json.loads(run_path.read_text())["step_budget"] == 3
    assert json.loads(summary_path.read_text())["step_budget"] == 3


def test_run_kernel_episode_threads_policy_id_to_engine(monkeypatch):
    captured = {}

    class StubKernel:
        def __init__(self, *, seed, policy_id):
            captured["seed"] = seed
            captured["policy_id"] = policy_id

        def run(self, assembly, max_steps):
            captured["max_steps"] = max_steps
            return assembly, []

    monkeypatch.setattr(kernel_experiments, "VectorGSKernelV1", StubKernel)

    episode = run_kernel_episode(seed=3, max_steps=5, policy_id="rule_uniform_random_v1")

    assert captured == {"seed": 3, "policy_id": "rule_uniform_random_v1", "max_steps": 5}
    assert episode["policy_id"] == "rule_uniform_random_v1"


def test_run_kernel_episode_rejects_unknown_policy():
    with pytest.raises(ValueError, match="Unsupported kernel policy_id"):
        run_kernel_episode(seed=0, max_steps=4, policy_id="unknown_policy_v1")


def test_diversity_episode_records_scenario_identity_and_is_deterministic():
    first = run_kernel_episode(
        seed=7,
        max_steps=12,
        scenario_builder=make_michell_diversity_cantilever_scenario,
        policy_id="rule_uniform_random_v1",
    )
    second = run_kernel_episode(
        seed=7,
        max_steps=12,
        scenario_builder=make_michell_diversity_cantilever_scenario,
        policy_id="rule_uniform_random_v1",
    )

    assert first["problem_id"] == "michell_diversity_cantilever_v1"
    assert first["scenario_name"] == "michell_diversity_cantilever_v1"
    assert first["trace"] == second["trace"]
    assert first["assembly"].to_data() == second["assembly"].to_data()
