from math import acos
from math import pi
from math import sqrt

from morph_engine.grammar.rules.split_node_rule import SplitNodeRule
from morph_engine.model.structural_graph import StructuralGraph


def _vector(a, b):
    return [b[i] - a[i] for i in range(3)]


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _mag(v):
    return sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def test_split_node_rule_creates_two_nodes_and_members():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0), fixed=[0, 0, 0])
    graph.set_temp_force("0", [1.0, 0.0, 0.0])

    rule = SplitNodeRule(theta_min=pi / 6.0, theta_max=pi / 6.0, length=2.0, seed=7)
    candidate = rule.propose(graph)[0]
    new_graph = rule.apply(graph, candidate.payload)

    assert new_graph.network.number_of_nodes() == 3
    assert new_graph.network.number_of_edges() == 2


def test_split_node_rule_branch_angles_correct():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0), fixed=[0, 0, 0])
    graph.set_temp_force("0", [1.0, 0.0, 0.0])

    theta = pi / 6.0
    rule = SplitNodeRule(theta_min=theta, theta_max=theta, length=2.0, seed=0)
    candidate = rule.propose(graph)[0]
    new_graph = rule.apply(graph, candidate.payload)

    origin = new_graph.network.node_attribute("0", "xyz")
    branch_keys = [str(k) for k in new_graph.network.nodes() if str(k) != "0"]
    v1 = _vector(origin, new_graph.network.node_attribute(branch_keys[0], "xyz"))
    v2 = _vector(origin, new_graph.network.node_attribute(branch_keys[1], "xyz"))

    angle = acos(max(-1.0, min(1.0, _dot(v1, v2) / (_mag(v1) * _mag(v2)))))
    assert abs(angle - 2.0 * theta) < 1e-9


def test_split_node_rule_decomposes_force_across_branches():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0), fixed=[0, 0, 0])
    graph.set_temp_force("0", [0.0, -10.0, 0.0])

    theta = pi / 6.0
    rule = SplitNodeRule(theta_min=theta, theta_max=theta, length=2.0, seed=0)
    candidate = rule.propose(graph)[0]
    new_graph = rule.apply(graph, candidate.payload)

    branch_keys = sorted([str(k) for k in new_graph.network.nodes() if str(k) != "0"])
    force_a = new_graph.get_temp_force(branch_keys[0])
    force_b = new_graph.get_temp_force(branch_keys[1])

    assert force_a != [0.0, -10.0, 0.0]
    assert force_b != [0.0, -10.0, 0.0]
    assert abs(force_a[0] + force_b[0]) < 1e-9
    assert abs((force_a[1] + force_b[1]) - (-10.0)) < 1e-9
