from morph_engine.evaluator.channels.maxwell_v1 import MaxwellCountChannel
from morph_engine.evaluator.evaluator import Evaluator
from morph_engine.model.structural_graph import StructuralGraph


def test_maxwell_redundancy_proxy():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[1, 1, 1])
    graph.add_node("1", (1, 0, 0), fixed=[0, 0, 0])
    graph.add_edge("0", "1")

    evaluator = Evaluator([MaxwellCountChannel()])
    result = evaluator.evaluate(graph)

    assert result["valid"] is True
    assert result["metrics"]["node_count"] == 2
    assert result["metrics"]["edge_count"] == 1
    assert result["metrics"]["restrained_dof"] == 3
    assert result["metrics"]["redundancy_proxy"] == -2
    assert result["signals"]["redundancy_proxy"] == -2
