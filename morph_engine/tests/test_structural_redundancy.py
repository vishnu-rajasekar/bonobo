from morph_engine.evaluator.channels.structural_redundancy_v1 import StructuralRedundancyChannel
from morph_engine.model.structural_graph import StructuralGraph


def test_structural_redundancy_3d_two_nodes_one_member():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[1, 1, 1])
    graph.add_node("1", (1, 0, 0), fixed=[1, 1, 1])
    graph.add_edge("0", "1")

    channel = StructuralRedundancyChannel(dimension=3)
    result = channel.evaluate(graph)

    assert result["metrics"]["joints"] == 2
    assert result["metrics"]["members"] == 1
    assert result["metrics"]["reaction_dof"] == 6
    assert result["metrics"]["redundancy_index"] == 1


def test_structural_redundancy_2d_triangle_isostatic():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[1, 1, 0])
    graph.add_node("1", (1, 0, 0), fixed=[0, 1, 0])
    graph.add_node("2", (0.5, 1, 0), fixed=[0, 0, 0])
    graph.add_edge("0", "1")
    graph.add_edge("1", "2")
    graph.add_edge("2", "0")

    channel = StructuralRedundancyChannel(dimension=2)
    result = channel.evaluate(graph)

    assert result["metrics"]["joints"] == 3
    assert result["metrics"]["members"] == 3
    assert result["metrics"]["reaction_dof"] == 3
    assert result["metrics"]["redundancy_index"] == 0
