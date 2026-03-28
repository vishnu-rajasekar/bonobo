import os
import tempfile

from morph_engine.experiments.artifacts_v1 import export_ml_ready
from morph_engine.experiments.artifacts_v1 import extract_graph_descriptors
from morph_engine.experiments.artifacts_v1 import benchmark_graph_diagnostics
from morph_engine.experiments.benchmark_scenarios import get_benchmark_scenario
from morph_engine.experiments.generate_structure import StructureGenerationExperiment
from morph_engine.experiments.logger_v1 import ExperimentLogger
from morph_engine.model.structural_graph import StructuralGraph


def test_benchmark_run_emits_required_artifacts():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ExperimentLogger(base_path=tmpdir)
        scenario = get_benchmark_scenario()
        scenario["max_iterations"] = 4

        experiment = StructureGenerationExperiment(scenario=scenario, logger=logger)
        graph, result, run_dir = experiment.run()

        assert graph is not None
        assert os.path.isdir(run_dir)
        assert result["summary"]["scenario_name"] == scenario["scenario_name"]
        assert "structural_dna" in result
        assert "graph_descriptors" in result
        assert "accepted_graph_digest" in result
        assert "ml_export" in result
        assert "artifact_paths" in result
        assert "trace_excerpt" in result
        assert result["trace"][0]["selected_rule_status"] == "initial_state"
        assert result["summary"]["support_trend"]["accepted_steps_improved_residual"] >= 0
        assert scenario["load_vector"] == [0.0, -10.0, 0.0]

        expected_files = {
            "accepted_graph_digest.json",
            "config.json",
            "explored_geometry_digest.json",
            "final_graph.json",
            "graph_descriptors.json",
            "metrics.json",
            "ml_export.json",
            "scenario.json",
            "structural_dna.json",
            "summary.json",
            "trace.json",
            "trace_excerpt.json",
        }
        assert expected_files.issubset(set(os.listdir(run_dir)))


def test_primary_benchmark_seed_has_no_support_to_load_edges():
    scenario = get_benchmark_scenario("mitchell_planar_benchmark_v1")
    experiment = StructureGenerationExperiment(scenario=scenario)
    graph = experiment.initialize_graph()

    assert graph.network.number_of_edges() == 0


def test_secondary_sanity_benchmark_keeps_legacy_seed_edges():
    scenario = get_benchmark_scenario("two_support_planar_sanity_v1")
    experiment = StructureGenerationExperiment(scenario=scenario)
    graph = experiment.initialize_graph()

    assert graph.network.number_of_edges() == 2


def test_descriptor_and_ml_export_capture_crossings():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0))
    graph.add_node("1", (1.0, 1.0, 0.0))
    graph.add_node("2", (0.0, 1.0, 0.0))
    graph.add_node("3", (1.0, 0.0, 0.0))
    graph.add_edge("0", "1")
    graph.add_edge("2", "3")
    graph.add_load("0", [0.0, -1.0, 0.0])
    graph.set_temp_force("0", [0.0, -1.0, 0.0])

    evaluation_result = {
        "channels": {
            "global_equilibrium_v1": {
                "valid": False,
                "metrics": {"residual_magnitude": 1.0},
            }
        }
    }

    descriptors = extract_graph_descriptors(graph)
    ml_export = export_ml_ready(graph, evaluation_result)

    assert descriptors["crossing_edge_count"] == 1
    assert descriptors["connected_component_count"] == 2
    assert len(ml_export["node_features"]) == 4
    assert ml_export["global_features"][0] == 1.0
    assert ml_export["global_features"][4] == 1


def test_benchmark_diagnostics_flag_two_member_non_collinear_joint():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0), fixed=[1, 1, 1])
    graph.add_node("1", (1.0, 1.0, 0.0), fixed=[0, 0, 0])
    graph.add_node("2", (1.0, 0.0, 0.0), fixed=[0, 0, 0])
    graph.add_node("3", (0.0, 1.0, 0.0), fixed=[0, 0, 0])
    graph.add_edge("1", "2")
    graph.add_edge("1", "3")
    graph.add_load("0", [0.0, -1.0, 0.0])

    diagnostics = benchmark_graph_diagnostics(graph, bounds={"min": [-2.0, -2.0], "max": [2.0, 2.0]})

    assert diagnostics["two_member_non_collinear_joint_count"] == 1
    assert diagnostics["two_member_non_collinear_joints"][0]["node_id"] == "1"
