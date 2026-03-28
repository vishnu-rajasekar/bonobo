from morph_engine.grammar.operators.force_ops import get_line_of_action
from morph_engine.grammar.operators.member_ops import get_member_force
from morph_engine.grammar.operators.member_ops import get_member_nodes
from morph_engine.grammar.operators.node_ops import equilibrate_node
from morph_engine.model.structural_graph import StructuralGraph


def test_get_line_of_action_returns_normalized_temp_force():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0))
    graph.set_temp_force("0", [3.0, 4.0, 0.0])

    loa = get_line_of_action(graph, "0")

    assert loa is not None
    assert loa["point"] == [0.0, 0.0, 0.0]
    assert abs(loa["direction"][0] - 0.6) < 1e-9
    assert abs(loa["direction"][1] - 0.8) < 1e-9


def test_equilibrate_node_returns_closing_vector():
    result = equilibrate_node([[1.0, 0.0, 0.0], [0.0, 2.0, 0.0]])

    assert result["closing_vector"] == [-1.0, -2.0, -0.0]
    assert abs(result["residual_magnitude"] - (5.0 ** 0.5)) < 1e-9
    assert result["closed"] is False


def test_member_ops_read_nodes_and_force_metadata():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0))
    graph.add_node("1", (2.0, 0.0, 0.0))
    graph.add_edge("0", "1", family="bar", force={"magnitude": 5.0, "direction": "compression"})

    nodes = get_member_nodes(graph, "0", "1")
    force = get_member_force(graph, "0", "1")

    assert nodes["u"] == "0"
    assert nodes["v"] == "1"
    assert nodes["u_xyz"] == [0.0, 0.0, 0.0]
    assert nodes["v_xyz"] == [2.0, 0.0, 0.0]
    assert force == {"magnitude": 5.0, "direction": "compression"}
