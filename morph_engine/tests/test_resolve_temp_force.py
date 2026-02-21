from morph_engine.grammar.rules.resolve_temp_force_v1 import ResolveTempForceV1
from morph_engine.model.structural_graph import StructuralGraph


def _has_edge(network, u, v):
    try:
        return network.has_edge((u, v))
    except TypeError:
        return network.has_edge(u, v)


def test_resolve_temp_force_transfers_force_to_new_node():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[0, 0, 0])
    graph.set_temp_force("0", [3, 0, 0])

    rule = ResolveTempForceV1()
    candidates = rule.propose(graph)
    new_graph = rule.apply(graph, candidates[0].payload)

    assert new_graph.network.number_of_nodes() == 2
    assert new_graph.get_temp_force("0") == [0.0, 0.0, 0.0]

    new_nodes = [k for k in new_graph.network.nodes() if str(k) != "0"]
    assert len(new_nodes) == 1
    new_key = new_nodes[0]
    assert new_graph.get_temp_force(new_key) == [3.0, 0.0, 0.0]
    assert _has_edge(new_graph.network, "0", new_key)
