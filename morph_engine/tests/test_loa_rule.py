from morph_engine.grammar.rules.loa_intersection_rule import LOAIntersectionRule
from morph_engine.model.structural_graph import StructuralGraph


def _has_edge(network, u, v):
    try:
        return network.has_edge((u, v))
    except TypeError:
        return network.has_edge(u, v)


def test_intersecting_temp_forces_create_new_node():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[0, 0, 0])
    graph.add_node("1", (1, 0, 0), fixed=[0, 0, 0])
    graph.set_temp_force("0", [1, 1, 0])
    graph.set_temp_force("1", [-1, 1, 0])

    rule = LOAIntersectionRule()
    candidates = rule.propose(graph)
    assert candidates

    new_graph = rule.apply(graph, candidates[0].payload)
    assert new_graph.network.number_of_nodes() == 3


def test_parallel_temp_forces_do_not_create_node():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[0, 0, 0])
    graph.add_node("1", (0, 1, 0), fixed=[0, 0, 0])
    graph.set_temp_force("0", [1, 0, 0])
    graph.set_temp_force("1", [1, 0, 0])

    rule = LOAIntersectionRule()
    candidates = rule.propose(graph)
    assert candidates == []


def test_loa_result_contains_two_new_members():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[0, 0, 0])
    graph.add_node("1", (1, 0, 0), fixed=[0, 0, 0])
    graph.set_temp_force("0", [1, 1, 0])
    graph.set_temp_force("1", [-1, 1, 0])

    rule = LOAIntersectionRule()
    candidates = rule.propose(graph)
    new_graph = rule.apply(graph, candidates[0].payload)

    assert new_graph.network.number_of_edges() == 2
    new_key = [k for k in new_graph.network.nodes() if str(k) not in ("0", "1")][0]
    assert _has_edge(new_graph.network, "0", new_key)
    assert _has_edge(new_graph.network, "1", new_key)
