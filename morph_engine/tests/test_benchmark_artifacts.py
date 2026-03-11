import os
import tempfile

from morph_engine.experiments.artifacts_v1 import export_ml_ready
from morph_engine.experiments.artifacts_v1 import extract_graph_descriptors
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
        assert result["trace"][0]["selected_rule_status"] == "initial_state"

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
        }
        assert expected_files.issubset(set(os.listdir(run_dir)))


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
