from morph_engine.evaluator.channels.global_equilibrium_v1 import GlobalEquilibriumChannel
from morph_engine.model.structural_graph import StructuralGraph


def test_global_equilibrium_with_balancing_reaction():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[1, 1, 1])
    graph.add_load("0", [0, -10, 0])

    channel = GlobalEquilibriumChannel()
    context = {
        "reaction_absorption_v1": {
            "metrics": {
                "total_reaction": [0, 10, 0],
            }
        }
    }

    result = channel.evaluate(graph, context=context)

    assert result["metrics"]["residual_vector"] == [0.0, 0.0, 0.0]
    assert result["metrics"]["residual_magnitude"] == 0.0
    assert result["valid"] is True


def test_global_equilibrium_without_reaction():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[1, 1, 1])
    graph.add_load("0", [0, -10, 0])

    channel = GlobalEquilibriumChannel()
    result = channel.evaluate(graph)

    assert result["metrics"]["residual_vector"] == [0.0, -10.0, 0.0]
    assert result["metrics"]["residual_magnitude"] == 10.0
    assert result["valid"] is False
