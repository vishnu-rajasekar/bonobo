from morph_engine.evaluator.channels.global_equilibrium_v1 import GlobalEquilibriumChannel
from morph_engine.evaluator.channels.reaction_absorption_v1 import ReactionAbsorptionChannel
from morph_engine.evaluator.channels.structural_redundancy_v1 import StructuralRedundancyChannel
from morph_engine.evaluator.channels.unbalanced_force_v1 import UnbalancedForceChannel
from morph_engine.evaluator.evaluator import Evaluator
from morph_engine.model.structural_graph import StructuralGraph


def test_evaluator_pipeline_context_and_validity():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[1, 1, 1])
    graph.set_temp_force("0", [0, -10, 0])
    graph.add_load("0", [0, -10, 0])

    evaluator = Evaluator(
        [
            ReactionAbsorptionChannel(),
            UnbalancedForceChannel(),
            GlobalEquilibriumChannel(),
            StructuralRedundancyChannel(dimension=3),
        ]
    )
    result = evaluator.evaluate(graph)

    channels = result["channels"]
    assert "reaction_absorption_v1" in channels
    assert "unbalanced_force_v1" in channels
    assert "global_equilibrium_v1" in channels
    assert "structural_redundancy_v1" in channels

    assert result["valid"] is True
    assert channels["global_equilibrium_v1"]["metrics"]["residual_magnitude"] == 0.0
    assert "redundancy_index" in channels["structural_redundancy_v1"]["metrics"]
