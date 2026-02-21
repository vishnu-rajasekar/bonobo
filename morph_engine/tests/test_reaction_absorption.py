from morph_engine.evaluator.channels.reaction_absorption_v1 import ReactionAbsorptionChannel
from morph_engine.model.structural_graph import StructuralGraph


def test_reaction_absorption_fully_fixed_node():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[1, 1, 1])
    graph.set_temp_force("0", [3, 4, 0])

    channel = ReactionAbsorptionChannel()
    result = channel.evaluate(graph)

    assert graph.get_temp_force("0") == [0.0, 0.0, 0.0]
    assert result["signals"]["reactions_by_node"]["0"] == [-3.0, -4.0, -0.0]
    assert result["metrics"]["total_reaction"] == [-3.0, -4.0, 0.0]
    assert result["metrics"]["reaction_count"] == 1


def test_reaction_absorption_partial_fixed_node():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[1, 0, 0])
    graph.set_temp_force("0", [3, 4, 0])

    channel = ReactionAbsorptionChannel()
    result = channel.evaluate(graph)

    assert graph.get_temp_force("0") == [0.0, 4.0, 0.0]
    assert result["signals"]["reactions_by_node"]["0"] == [-3.0, 0.0, 0.0]
