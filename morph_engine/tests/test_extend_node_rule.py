from morph_engine.grammar.rules.extend_node_rule import ExtendNodeRule
from morph_engine.model.structural_graph import StructuralGraph


def test_extend_node_rule_adds_node_and_member():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0), fixed=[0, 0, 0])
    graph.set_temp_force("0", [3.0, 4.0, 0.0])

    rule = ExtendNodeRule(lmin=2.0, lmax=2.0, seed=42)
    candidates = rule.propose(graph)
    assert len(candidates) == 1

    new_graph = rule.apply(graph, candidates[0].payload)

    assert new_graph.network.number_of_nodes() == 2
    assert new_graph.network.number_of_edges() == 1


def test_extend_node_rule_places_node_along_force_direction():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0), fixed=[0, 0, 0])
    graph.set_temp_force("0", [3.0, 4.0, 0.0])

    rule = ExtendNodeRule(lmin=2.0, lmax=2.0, seed=0)
    candidate = rule.propose(graph)[0]
    new_graph = rule.apply(graph, candidate.payload)

    new_key = [str(k) for k in new_graph.network.nodes() if str(k) != "0"][0]
    xyz = new_graph.network.node_attribute(new_key, "xyz")

    assert abs(xyz[0] - 1.2) < 1e-9
    assert abs(xyz[1] - 1.6) < 1e-9
    assert abs(xyz[2] - 0.0) < 1e-9
