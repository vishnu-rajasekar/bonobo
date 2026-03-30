from morph_engine.grammar.rules.triangle_closure_rule import TriangleClosureRule
from morph_engine.model.structural_graph import StructuralGraph
from morph_engine.semantics import member_force_record


def _has_edge(network, u, v):
    try:
        return network.has_edge((u, v))
    except TypeError:
        return network.has_edge(u, v)


def test_triangle_closure_creates_triangle_member():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0), fixed=[0, 0, 0])
    graph.add_node("1", (1.0, 0.0, 0.0), fixed=[0, 0, 0])
    graph.add_node("2", (2.0, 0.0, 0.0), fixed=[0, 0, 0])
    graph.add_edge("0", "1", family="bar")
    graph.add_edge("1", "2", family="bar")

    rule = TriangleClosureRule(radius=5.0)
    candidates = rule.propose(graph)
    assert candidates

    new_graph = rule.apply(graph, candidates[0].payload)

    assert new_graph.network.number_of_edges() == 3
    assert _has_edge(new_graph.network, "0", "2")
    force = member_force_record(new_graph, "0", "2")
    assert force is not None
    assert force["metadata"]["semantic_origin"] == "triangle_closure"


def test_triangle_closure_avoids_duplicates():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0), fixed=[0, 0, 0])
    graph.add_node("1", (1.0, 0.0, 0.0), fixed=[0, 0, 0])
    graph.add_node("2", (2.0, 0.0, 0.0), fixed=[0, 0, 0])
    graph.add_edge("0", "1", family="bar")
    graph.add_edge("1", "2", family="bar")

    rule = TriangleClosureRule(radius=5.0)
    first = rule.propose(graph)[0]
    closed_graph = rule.apply(graph, first.payload)

    assert not rule.propose(closed_graph)
    assert closed_graph.network.number_of_edges() == 3


def test_triangle_closure_detects_shared_parent_path_regardless_of_node_order():
    graph = StructuralGraph()
    graph.add_node("2", (0.0, 0.0, 0.0), fixed=[0, 0, 0])
    graph.add_node("3", (1.0, 0.0, 0.0), fixed=[0, 0, 0])
    graph.add_node("4", (-1.0, 0.0, 0.0), fixed=[0, 0, 0])
    graph.add_edge("2", "3", family="bar")
    graph.add_edge("2", "4", family="bar")

    rule = TriangleClosureRule(radius=3.0)
    candidates = rule.propose(graph)

    assert any({candidate.payload["u"], candidate.payload["v"]} == {"3", "4"} for candidate in candidates)
