from morph_engine.evaluator.channels.unbalanced_force_v1 import UnbalancedForceChannel
from morph_engine.model.structural_graph import StructuralGraph


def test_unbalanced_force_empty_graph():
    graph = StructuralGraph()
    channel = UnbalancedForceChannel()

    result = channel.evaluate(graph)

    assert result["metrics"]["global_imbalance"] == 0
    assert result["metrics"]["max_node_imbalance"] == 0
    assert result["signals"]["done"] is True


def test_unbalanced_force_single_node():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[0, 0, 0])
    graph.set_temp_force("0", [3, 4, 0])
    channel = UnbalancedForceChannel()

    result = channel.evaluate(graph)

    assert result["metrics"]["global_imbalance"] == 5
    assert result["metrics"]["max_node_imbalance"] == 5
    assert result["signals"]["done"] is False


def test_unbalanced_force_opposite_forces_do_not_cancel():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[0, 0, 0])
    graph.add_node("1", (1, 0, 0), fixed=[0, 0, 0])
    graph.set_temp_force("0", [1, 0, 0])
    graph.set_temp_force("1", [-1, 0, 0])
    channel = UnbalancedForceChannel()

    result = channel.evaluate(graph)

    assert result["metrics"]["global_imbalance"] == 2
