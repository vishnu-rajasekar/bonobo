from morph_engine.experiments.benchmark_scenarios import get_benchmark_recovery_modes
from morph_engine.evaluator.channels.global_equilibrium_v1 import GlobalEquilibriumChannel
from morph_engine.evaluator.channels.reaction_absorption_v1 import ReactionAbsorptionChannel
from morph_engine.evaluator.evaluator import Evaluator
from morph_engine.grammar.rules.resolve_two_forces_rule import ResolveTwoForcesRule
from morph_engine.grammar.rules.single_node_root_link_rule import SingleNodeRootLinkRule
from morph_engine.model.structural_graph import StructuralGraph
from morph_engine.semantics import member_force_record


def test_recovery_modes_are_explicit_and_unseeded():
    modes = get_benchmark_recovery_modes()

    assert [mode["comparison_mode"] for mode in modes] == ["A", "B", "C", "D"]
    assert all(mode.get("seed_support_to_load_edges") is False for mode in modes)
    assert "resolve_two_forces_rule" in modes[1]["enabled_rules"]
    assert "bidirectional_loa_intersection_rule" in modes[2]["enabled_rules"]
    assert "single_node_root_link_rule" in modes[3]["enabled_rules"]


def test_resolve_two_forces_rule_connects_aligned_active_nodes():
    graph = StructuralGraph()
    graph.add_node("0", (0.0, 0.0, 0.0))
    graph.add_node("1", (1.0, 0.0, 0.0))
    graph.set_temp_force("0", [1.0, 0.0, 0.0])
    graph.set_temp_force("1", [-1.0, 0.0, 0.0])

    rule = ResolveTwoForcesRule()
    actions = rule.propose(graph)
    assert len(actions) == 1

    new_graph = rule.apply(graph, actions[0].payload)
    assert new_graph.network.number_of_edges() == 1
    assert new_graph.get_temp_force("0") == [0.0, 0.0, 0.0]
    assert new_graph.get_temp_force("1") == [0.0, 0.0, 0.0]
    force = member_force_record(new_graph, "0", "1")
    assert force is not None
    assert force["metadata"]["semantic_origin"] == "resolve_two_forces"


def test_single_node_root_link_rule_applies_to_one_active_front():
    graph = StructuralGraph()
    graph.add_node("0", (-5.0, 0.0, 0.0), fixed=[1, 1, 1])
    graph.add_node("1", (-5.0, 4.0, 0.0), fixed=[1, 1, 1])
    graph.add_node("2", (5.0, 2.0, 0.0))
    graph.add_node("3", (5.0, 0.3, 0.0))
    graph.add_edge("2", "3", family="bar")
    graph.set_temp_force("3", [0.0, -10.0, 0.0])

    rule = SingleNodeRootLinkRule()
    actions = rule.propose(graph)

    assert len(actions) == 1


def test_single_node_root_link_rule_can_propose_for_multiple_active_fronts():
    graph = StructuralGraph()
    graph.add_node("0", (-5.0, 0.0, 0.0), fixed=[1, 1, 1])
    graph.add_node("1", (-5.0, 4.0, 0.0), fixed=[1, 1, 1])
    graph.add_node("2", (0.0, 2.0, 0.0))
    graph.add_node("3", (1.0, 2.0, 0.0))
    graph.add_edge("2", "3", family="bar")
    graph.set_temp_force("2", [-1.0, 0.0, 0.0])
    graph.set_temp_force("3", [-1.0, 0.0, 0.0])

    rule = SingleNodeRootLinkRule()
    actions = rule.propose(graph)

    assert len(actions) == 2


def test_single_node_root_link_to_support_transfers_temp_force_for_absorption():
    graph = StructuralGraph()
    graph.add_node("0", (-5.0, 0.0, 0.0), fixed=[1, 1, 1])
    graph.add_node("1", (5.0, 0.0, 0.0))
    graph.add_edge("0", "1", family="bar")
    graph.add_load("1", [0.0, -10.0, 0.0])
    graph.set_temp_force("1", [0.0, -10.0, 0.0])

    rule = SingleNodeRootLinkRule()
    new_graph = rule.apply(
        graph,
        {
            "source_node": "1",
            "target_kind": "support_node",
            "target_node": "0",
            "target_xyz": [-5.0, 0.0, 0.0],
        },
    )

    assert new_graph.get_temp_force("1") == [0.0, 0.0, 0.0]
    assert new_graph.get_temp_force("0") == [0.0, -10.0, 0.0]
    force = member_force_record(new_graph, "0", "1")
    assert force is not None
    assert force["metadata"]["semantic_origin"] == "single_node_root_link"

    result = Evaluator([ReactionAbsorptionChannel(), GlobalEquilibriumChannel()]).evaluate(new_graph)
    assert result["channels"]["reaction_absorption_v1"]["metrics"]["absorbed_magnitude"] > 0.0
    assert result["channels"]["global_equilibrium_v1"]["metrics"]["residual_magnitude"] == 0.0
