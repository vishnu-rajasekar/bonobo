from morph_engine.grammar.rules.create_node_rule import CreateNodeRule
from morph_engine.grammar.operators.force_ops import get_line_of_action
from morph_engine.grammar.rules.extend_node_rule import ExtendNodeRule
from morph_engine.grammar.rules.split_node_rule import SplitNodeRule
from morph_engine.model.structural_graph import StructuralGraph
from morph_engine.semantics import build_structural_assembly_view
from morph_engine.semantics import build_structural_node_view
from morph_engine.semantics import member_force_record


def test_structural_node_view_collects_load_temp_and_member_semantics():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0))
    graph.add_node("1", (2.0, 0.0, 0.0))
    graph.add_edge("0", "1", family="bar", force={"vector": [2.0, 0.0, 0.0], "source_node": "0"})
    graph.add_load("0", [0.0, -5.0, 0.0])
    graph.set_temp_force("0", [1.0, 0.0, 0.0])

    node_view = build_structural_node_view(graph, "0")

    assert node_view.node_id == "0"
    assert node_view.load is True
    assert node_view.active is True
    assert len(node_view.member_forces) == 1
    assert len(node_view.temp_forces) == 1
    assert any(force.kind == "load" for force in node_view.local_forces)


def test_structural_assembly_view_tracks_active_fronts():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0), fixed=[1, 1, 1])
    graph.add_node("1", (1.0, 0.0, 0.0))
    graph.set_temp_force("1", [1.0, 0.0, 0.0])

    assembly_view = build_structural_assembly_view(graph)

    assert assembly_view.support_node_ids == ["0"]
    assert assembly_view.active_front_ids == ["1"]


def test_structural_node_view_reads_explicit_graph_node_forces():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0))
    graph.add_force_to_node(
        "0",
        {
            "kind": "temporary",
            "vector": [2.0, 0.0, 0.0],
            "status": "provisional",
            "provenance": "unit_test",
            "metadata": {"semantic_origin": "test_seed"},
        },
    )

    node_view = build_structural_node_view(graph, "0")

    assert node_view.active is True
    assert any(force.provenance == "unit_test" for force in node_view.local_forces)


def test_get_line_of_action_uses_structural_node_view():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0))
    graph.set_temp_force("0", [3.0, 4.0, 0.0])

    loa = get_line_of_action(graph, "0")

    assert loa is not None
    assert loa["point"] == [0.0, 0.0, 0.0]
    assert abs(loa["direction"][0] - 0.6) < 1e-9
    assert abs(loa["direction"][1] - 0.8) < 1e-9


def test_extend_node_rule_records_member_force_semantics():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0))
    graph.set_temp_force("0", [3.0, 4.0, 0.0])

    rule = ExtendNodeRule(lmin=2.0, lmax=2.0, seed=0)
    candidate = rule.propose(graph)[0]
    new_graph = rule.apply(graph, candidate.payload)

    new_key = [str(k) for k in new_graph.network.nodes() if str(k) != "0"][0]
    force = member_force_record(new_graph, "0", new_key)

    assert force is not None
    assert force["metadata"]["semantic_origin"] == "extend_node"
    assert force["source_node"] == "0"
    assert force["vector"] == [3.0, 4.0, 0.0]


def test_split_node_rule_records_branch_member_force_semantics():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0))
    graph.set_temp_force("0", [0.0, -10.0, 0.0])

    rule = SplitNodeRule(theta_min=0.4, theta_max=0.4, length=2.0, seed=0)
    candidate = rule.propose(graph)[0]
    new_graph = rule.apply(graph, candidate.payload)

    branch_keys = sorted([str(k) for k in new_graph.network.nodes() if str(k) != "0"])
    force_a = member_force_record(new_graph, "0", branch_keys[0])
    force_b = member_force_record(new_graph, "0", branch_keys[1])

    assert force_a is not None
    assert force_b is not None
    assert force_a["metadata"]["semantic_origin"] == "split_node"
    assert force_b["metadata"]["semantic_origin"] == "split_node"


def test_create_node_rule_creates_floating_seed_with_explicit_force_semantics():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0))
    graph.set_temp_force("0", [0.0, -10.0, 0.0])

    rule = CreateNodeRule(lmin=2.0, lmax=2.0, angle_min=0.0, angle_max=0.0, seed=0)
    candidate = rule.propose(graph)[0]
    new_graph = rule.apply(graph, candidate.payload)

    created = [str(key) for key in new_graph.network.nodes() if str(key) != "0"][0]
    created_view = build_structural_node_view(new_graph, created)

    assert new_graph.network.number_of_edges() == 0
    assert created_view.active is True
    assert any(force.metadata.get("semantic_origin") == "create_node" for force in created_view.local_forces)
