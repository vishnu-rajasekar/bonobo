#!/usr/bin/env python3
"""Prespecified Phase 0C parameter-regime study for the VectorGS baseline."""

import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from datetime import datetime
from datetime import timezone
from functools import partial
from math import comb
from math import pi
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "morph_engine"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from morph_engine.vector_gs_kernel_v1.engine import GDGS_NODE_RULE_UNIFORM_POLICY_ID
from morph_engine.vector_gs_kernel_v1.experiments import run_kernel_episode
from morph_engine.vector_gs_kernel_v1.export import export_run
from morph_engine.vector_gs_kernel_v1.rules import RuleParameterConfiguration
from morph_engine.vector_gs_kernel_v1.scenarios import ReactionAngleConfiguration
from morph_engine.vector_gs_kernel_v1.scenarios import make_default_cantilever_scenario


SCHEMA_VERSION = "1.1"
STUDY_ID = "vector_gs_parameter_readiness_v1_r4"
HISTORICAL_BASELINE_COMMIT = "87bd7f3b9113f0ac74e4548b0301b9668086479f"
EXPLORATORY_SEEDS = list(range(0, 30))
CONFIRMATORY_SEEDS = list(range(30, 100))
STEP_BUDGET = 30
REACTION_ANGLES_DEGREES = [10.0, 18.43494882292201, 27.0]
GROWTH_LIMITS = [2, 4, 6, 8]


def rule_profiles():
    return {
        "current_reference": RuleParameterConfiguration(),
        "full_rotation_explicit_cutoffs": RuleParameterConfiguration(
            configuration_id="full_rotation_explicit_cutoffs_v1",
            create_min_rotation=-pi,
            create_max_rotation=pi,
            create_growth_step_limit=12,
            extend_growth_step_limit=12,
            split_growth_step_limit=12,
        ),
        "bounded_rotation_90": RuleParameterConfiguration(
            configuration_id="bounded_rotation_90_v1",
            create_min_rotation=-pi / 2.0,
            create_max_rotation=pi / 2.0,
            create_growth_step_limit=12,
            extend_growth_step_limit=12,
            split_growth_step_limit=12,
        ),
        "bounded_rotation_30": RuleParameterConfiguration(
            configuration_id="bounded_rotation_30_v1",
            create_min_rotation=-pi / 6.0,
            create_max_rotation=pi / 6.0,
            create_growth_step_limit=12,
            extend_growth_step_limit=12,
            split_growth_step_limit=12,
        ),
    }


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_state():
    tracked_diff = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--binary", "HEAD"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    status = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--short"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    relevant = [
        "morph_engine/morph_engine/vector_gs_kernel_v1/__init__.py",
        "morph_engine/morph_engine/vector_gs_kernel_v1/engine.py",
        "morph_engine/morph_engine/vector_gs_kernel_v1/experiments.py",
        "morph_engine/morph_engine/vector_gs_kernel_v1/operators.py",
        "morph_engine/morph_engine/vector_gs_kernel_v1/rules.py",
        "morph_engine/morph_engine/vector_gs_kernel_v1/scenarios.py",
        "scripts/run_vector_gs_parameter_readiness_v1.py",
    ]
    return {
        "head_commit": subprocess_commit(),
        "git_status": status,
        "tracked_diff_sha256": hashlib.sha256(tracked_diff.encode()).hexdigest(),
        "source_file_sha256": {
            path: sha256_file(REPO_ROOT / path) for path in relevant
        },
    }


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_jsonl(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records)
    )


def closure_diagnostics(record):
    final = record["trace"][-1] if record["trace"] else {}
    return final.get("params", {}).get("closure_diagnostics")


def compact_record(record, parameter_id, angle, growth_limit, profile_id):
    metrics = record["final_metrics"]
    diagnostic = closure_diagnostics(record)
    return {
        "parameter_id": parameter_id,
        "seed": record["seed"],
        "reaction_angle_degrees": angle,
        "growth_limit": growth_limit,
        "rule_profile_id": profile_id,
        "benchmark_complete": bool(metrics["benchmark_complete"]),
        "equilibrium_reached": bool(metrics["equilibrium_reached"]),
        "support_connected": bool(
            metrics["support_connectivity"]["support_connected"]
        ),
        "geometrically_valid": bool(
            metrics["benchmark_validity"]["geometrically_valid"]
        ),
        "termination_reason": record["termination_reason"],
        "node_count": len(record["assembly"].nodes),
        "member_count": len(record["assembly"].members),
        "total_member_length": metrics["material_proxy_total_member_length"],
        "final_residual_magnitude": metrics["final_residual_magnitude"],
        "closure_diagnostic_reason": (
            None if diagnostic is None else diagnostic.get("diagnostic_reason")
        ),
        "closure_rejection_counts": (
            {} if diagnostic is None else diagnostic.get("rejection_counts", {})
        ),
    }


def configuration_rows():
    rows = []
    for angle in REACTION_ANGLES_DEGREES:
        for growth_limit in GROWTH_LIMITS:
            for profile_id, profile in rule_profiles().items():
                parameter_id = "angle-{0:g}_growth-{1}_{2}".format(
                    angle, growth_limit, profile_id
                )
                rows.append(
                    {
                        "parameter_id": parameter_id,
                        "reaction_angle_degrees": angle,
                        "growth_limit": growth_limit,
                        "rule_profile_id": profile_id,
                        "rule_parameter_configuration": profile.to_data(),
                    }
                )
    return rows


def run_one(seed, row):
    reaction = ReactionAngleConfiguration(
        configuration_id="reaction_{0:g}deg_v1".format(
            row["reaction_angle_degrees"]
        ),
        lower_support_angle_degrees=row["reaction_angle_degrees"],
    )
    scenario_builder = partial(
        make_default_cantilever_scenario,
        reaction_configuration=reaction,
    )
    profile = rule_profiles()[row["rule_profile_id"]]
    record = run_kernel_episode(
        seed=seed,
        max_steps=STEP_BUDGET,
        scenario_builder=scenario_builder,
        policy_id=GDGS_NODE_RULE_UNIFORM_POLICY_ID,
        growth_limit=row["growth_limit"],
        rule_parameter_configuration=profile,
    )
    return record, compact_record(
        record,
        row["parameter_id"],
        row["reaction_angle_degrees"],
        row["growth_limit"],
        row["rule_profile_id"],
    )


def summarize(records):
    grouped = {}
    for record in records:
        grouped.setdefault(record["parameter_id"], []).append(record)
    summaries = []
    for parameter_id, group in sorted(grouped.items()):
        count = len(group)
        summaries.append(
            {
                "parameter_id": parameter_id,
                "run_count": count,
                "benchmark_complete_count": sum(
                    record["benchmark_complete"] for record in group
                ),
                "benchmark_completion_rate": sum(
                    record["benchmark_complete"] for record in group
                )
                / float(count),
                "support_connected_rate": sum(
                    record["support_connected"] for record in group
                )
                / float(count),
                "geometrically_valid_rate": sum(
                    record["geometrically_valid"] for record in group
                )
                / float(count),
                "termination_reason_counts": dict(
                    sorted(Counter(record["termination_reason"] for record in group).items())
                ),
                "mean_member_count": sum(
                    record["member_count"] for record in group
                )
                / float(count),
                "mean_total_member_length": sum(
                    record["total_member_length"] for record in group
                )
                / float(count),
                "reaction_angle_degrees": group[0]["reaction_angle_degrees"],
                "growth_limit": group[0]["growth_limit"],
                "rule_profile_id": group[0]["rule_profile_id"],
            }
        )
    return summaries


def select_configuration(summaries):
    """Select by completion, connectivity, lower growth, then greatest lexical ID."""
    return max(
        summaries,
        key=lambda item: (
            item["benchmark_completion_rate"],
            item["support_connected_rate"],
            -item["growth_limit"],
            item["parameter_id"],
        ),
    )


def paired_comparison(records, selected_parameter_id, reference_parameter_id):
    by_parameter = {}
    for record in records:
        by_parameter.setdefault(record["parameter_id"], {})[record["seed"]] = bool(
            record["benchmark_complete"]
        )
    selected = by_parameter[selected_parameter_id]
    reference = by_parameter[reference_parameter_id]
    seeds = sorted(set(selected) & set(reference))
    selected_only = sum(selected[seed] and not reference[seed] for seed in seeds)
    reference_only = sum(reference[seed] and not selected[seed] for seed in seeds)
    both = sum(reference[seed] and selected[seed] for seed in seeds)
    neither = sum(not reference[seed] and not selected[seed] for seed in seeds)
    discordant = selected_only + reference_only
    exact_p = 1.0
    if discordant:
        exact_p = min(
            1.0,
            2.0
            * sum(
                comb(discordant, index)
                for index in range(min(selected_only, reference_only) + 1)
            )
            / float(2**discordant),
        )
    return {
        "selected_parameter_id": selected_parameter_id,
        "reference_parameter_id": reference_parameter_id,
        "paired_seed_count": len(seeds),
        "selected_only": selected_only,
        "reference_only": reference_only,
        "both": both,
        "neither": neither,
        "paired_completion_rate_difference": (
            selected_only - reference_only
        )
        / float(len(seeds)),
        "exact_two_sided_mcnemar_p": exact_p,
        "interpretation": (
            "Descriptive held-out comparison of bundled parameter regimes; "
            "it does not identify an individual parameter effect."
        ),
    }


def historical_baseline_records():
    """Reproduce the untouched pre-Phase-0C implementation in an isolated archive."""
    archive = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "archive", HISTORICAL_BASELINE_COMMIT],
        capture_output=True,
        check=True,
    ).stdout
    program = """
import json
from morph_engine.vector_gs_kernel_v1.engine import GDGS_NODE_RULE_UNIFORM_POLICY_ID
from morph_engine.vector_gs_kernel_v1.experiments import run_kernel_episode

rows = []
for seed in range(30, 100):
    record = run_kernel_episode(
        seed=seed,
        max_steps=30,
        policy_id=GDGS_NODE_RULE_UNIFORM_POLICY_ID,
        growth_limit=4,
    )
    metrics = record["final_metrics"]
    rows.append({
        "parameter_id": "historical_baseline_87bd7f3",
        "seed": seed,
        "reaction_angle_degrees": 18.43494882292201,
        "growth_limit": 4,
        "rule_profile_id": "historical_baseline_87bd7f3",
        "benchmark_complete": bool(metrics["benchmark_complete"]),
        "equilibrium_reached": bool(metrics["equilibrium_reached"]),
        "support_connected": bool(metrics["support_connectivity"]["support_connected"]),
        "geometrically_valid": bool(metrics["benchmark_validity"]["geometrically_valid"]),
        "termination_reason": record["termination_reason"],
        "node_count": len(record["assembly"].nodes),
        "member_count": len(record["assembly"].members),
        "total_member_length": metrics["material_proxy_total_member_length"],
        "final_residual_magnitude": metrics["final_residual_magnitude"],
        "closure_diagnostic_reason": None,
        "closure_rejection_counts": {},
    })
print(json.dumps(rows, sort_keys=True))
"""
    with tempfile.TemporaryDirectory(prefix="bonobo-historical-baseline-") as temp:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as handle:
            handle.extractall(temp)
        environment = os.environ.copy()
        package_root = str(Path(temp) / "morph_engine")
        inherited = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = (
            package_root
            if not inherited
            else package_root + os.pathsep + inherited
        )
        result = subprocess.run(
            [sys.executable, "-c", program],
            cwd=temp,
            env=environment,
            text=True,
            capture_output=True,
            check=True,
        )
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        required=True,
        help="New external evidence directory; existing directories are refused.",
    )
    parser.add_argument(
        "--renderer",
        type=Path,
        help="Optional deterministic plan-view renderer for bound representative figures.",
    )
    args = parser.parse_args()
    output = Path(args.output_dir)
    if output.exists():
        raise SystemExit("output directory already exists: {0}".format(output))
    output.mkdir(parents=True)

    design = {
        "schema_version": SCHEMA_VERSION,
        "study_id": STUDY_ID,
        "study_type": "exploratory_calibration_then_held_out_confirmation",
        "primary_outcome": "benchmark_completion_rate including all runs",
        "selection_rule": [
            "highest exploratory benchmark completion rate",
            "then highest support connectivity rate",
            "then lower growth limit",
            "then lexicographically greatest parameter id",
        ],
        "exploratory_seeds": EXPLORATORY_SEEDS,
        "confirmatory_seeds": CONFIRMATORY_SEEDS,
        "seed_sets_disjoint": True,
        "step_budget": STEP_BUDGET,
        "reaction_angles_degrees": REACTION_ANGLES_DEGREES,
        "growth_limits": GROWTH_LIMITS,
        "rule_profiles": {
            key: value.to_data() for key, value in rule_profiles().items()
        },
        "configurations": configuration_rows(),
        "historical_baseline": {
            "commit": HISTORICAL_BASELINE_COMMIT,
            "purpose": (
                "Context only: this arm reproduces the implementation before "
                "the Phase 0C counter and closure changes and is not a pure parameter contrast."
            ),
        },
        "interpretation": (
            "This study maps bundled parameter-regime sensitivity on one current "
            "implementation. It does not identify individual causal parameter effects."
        ),
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    write_json(output / "study-design.json", design)

    exploratory = []
    for row in configuration_rows():
        for seed in EXPLORATORY_SEEDS:
            _, compact = run_one(seed, row)
            exploratory.append(compact)
    exploratory_summary = summarize(exploratory)
    selected = select_configuration(exploratory_summary)
    write_jsonl(output / "exploratory-runs.jsonl", exploratory)
    write_json(output / "exploratory-summary.json", exploratory_summary)
    write_json(output / "selection.json", selected)

    reference_id = next(
        row["parameter_id"]
        for row in configuration_rows()
        if row["rule_profile_id"] == "current_reference"
        and row["growth_limit"] == 4
        and abs(row["reaction_angle_degrees"] - 18.43494882292201) < 1e-9
    )
    confirm_ids = {reference_id, selected["parameter_id"]}
    confirm_rows = [
        row for row in configuration_rows() if row["parameter_id"] in confirm_ids
    ]
    confirmatory = []
    raw_root = output / "confirmatory-runs"
    for row in confirm_rows:
        for seed in CONFIRMATORY_SEEDS:
            record, compact = run_one(seed, row)
            confirmatory.append(compact)
            export_run(
                raw_root / row["parameter_id"] / "seed-{0:03d}".format(seed),
                record["assembly"],
                record["trace"],
                record["scenario_name"],
                seed,
                problem_id=record["problem_id"],
                policy_id=record["policy_id"],
                step_budget=record["step_budget"],
                termination_reason=record["termination_reason"],
                final_metrics=record["final_metrics"],
            )
    confirmatory_summary = summarize(confirmatory)
    write_jsonl(output / "confirmatory-runs.jsonl", confirmatory)
    write_json(output / "confirmatory-summary.json", confirmatory_summary)
    comparison = paired_comparison(
        confirmatory,
        selected["parameter_id"],
        reference_id,
    )
    write_json(output / "paired-comparison.json", comparison)

    historical = historical_baseline_records()
    write_jsonl(output / "historical-baseline-runs.jsonl", historical)
    write_json(output / "historical-baseline-summary.json", summarize(historical))

    representative_seed = next(
        (
            seed
            for seed in CONFIRMATORY_SEEDS
            if next(
                record["benchmark_complete"]
                for record in confirmatory
                if record["parameter_id"] == selected["parameter_id"]
                and record["seed"] == seed
            )
            and not next(
                record["benchmark_complete"]
                for record in confirmatory
                if record["parameter_id"] == reference_id
                and record["seed"] == seed
            )
        ),
        None,
    )
    figure_metadata = None
    if args.renderer is not None:
        renderer = args.renderer.resolve()
        if not renderer.is_file():
            raise SystemExit("renderer does not exist: {0}".format(renderer))
        if representative_seed is None:
            raise SystemExit("no selected-only held-out seed available for figures")
        figure_root = output / "figures"
        figure_root.mkdir()
        figure_specs = [
            (
                selected["parameter_id"],
                "seed-{0:03d}-selected.svg".format(representative_seed),
                "Seed {0} — selected bounded regime — complete".format(
                    representative_seed
                ),
            ),
            (
                reference_id,
                "seed-{0:03d}-current-reference.svg".format(
                    representative_seed
                ),
                "Seed {0} — current reference regime — incomplete".format(
                    representative_seed
                ),
            ),
        ]
        for parameter_id, filename, title in figure_specs:
            run_json = (
                raw_root
                / parameter_id
                / "seed-{0:03d}".format(representative_seed)
                / "kernel_run.json"
            )
            subprocess.run(
                [
                    sys.executable,
                    str(renderer),
                    str(run_json),
                    str(figure_root / filename),
                    "--title",
                    title,
                    "--dimensions",
                ],
                check=True,
            )
        figure_metadata = {
            "representative_seed": representative_seed,
            "renderer": str(renderer),
            "renderer_sha256": sha256_file(renderer),
            "fixed_extent_with_margin": True,
        }
        write_json(output / "figure-metadata.json", figure_metadata)

    files = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name not in {"MANIFEST.json", "SHA256SUMS.txt"}:
            files.append(
                {
                    "path": str(path.relative_to(output)),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "study_id": STUDY_ID,
        "source_state": source_state(),
        "selected_parameter_id": selected["parameter_id"],
        "current_reference_parameter_id": reference_id,
        "historical_baseline_commit": HISTORICAL_BASELINE_COMMIT,
        "exploratory_run_count": len(exploratory),
        "confirmatory_run_count": len(confirmatory),
        "historical_baseline_run_count": len(historical),
        "seed_sets_disjoint": not bool(
            set(EXPLORATORY_SEEDS) & set(CONFIRMATORY_SEEDS)
        ),
        "figure_metadata": figure_metadata,
        "files": files,
    }
    write_json(output / "MANIFEST.json", manifest)
    checksum_rows = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            checksum_rows.append(
                "{0}  {1}".format(sha256_file(path), path.relative_to(output))
            )
    (output / "SHA256SUMS.txt").write_text("\n".join(checksum_rows) + "\n")
    print(json.dumps({"manifest": str(output / "MANIFEST.json"), "selected": selected, "confirmatory": confirmatory_summary}, indent=2))


def subprocess_commit():
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
