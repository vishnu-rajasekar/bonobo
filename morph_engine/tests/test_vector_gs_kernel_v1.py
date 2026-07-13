import json
import pytest

from morph_engine.vector_gs_kernel_v1 import VectorGSKernelV1
from morph_engine.vector_gs_kernel_v1 import make_default_cantilever_scenario
from morph_engine.vector_gs_kernel_v1.model import Assembly
from morph_engine.vector_gs_kernel_v1.model import Force
from morph_engine.vector_gs_kernel_v1.model import ForceDirection
from morph_engine.vector_gs_kernel_v1.model import ForceKind
from morph_engine.vector_gs_kernel_v1.model import GenerationState
from morph_engine.vector_gs_kernel_v1.model import Member
from morph_engine.vector_gs_kernel_v1.model import Node
from morph_engine.vector_gs_kernel_v1.model import NodeType
from morph_engine.vector_gs_kernel_v1.metrics import compute_kernel_metrics
from morph_engine.vector_gs_kernel_v1.export import export_run
from morph_engine.vector_gs_kernel_v1.operators import connect_two_forces
from morph_engine.vector_gs_kernel_v1.operators import equilibrate_node
from morph_engine.vector_gs_kernel_v1.operators import segment_is_admissible
from morph_engine.vector_gs_kernel_v1.rules import RuleProposal
from morph_engine.vector_gs_kernel_v1.rules import CreateNodeRule
from morph_engine.vector_gs_kernel_v1.rules import ExtendNodeRule
from morph_engine.vector_gs_kernel_v1.rules import CloseStructureRule
from morph_engine.vector_gs_kernel_v1.rules import SplitNodeRule
from morph_engine.vector_gs_kernel_v1.scenarios import make_concurrent_three_force_smoke_scenario
from morph_engine.vector_gs_kernel_v1.scenarios import make_michell_diversity_cantilever_scenario


BOUNDARY = {"min": [-1.0, -1.0, 0.0], "max": [6.0, 6.0, 0.0]}


def test_equilibrate_node_adds_temp_force():
    node = Node(
        "0",
        [0.0, 0.0, 0.0],
        NodeType.FLOAT,
        forces=[
            Force([0.0, 0.0, 0.0], [1.0, 0.0, 0.0], ForceKind.MEMBER, ForceDirection.COMPRESSION),
            Force([0.0, 0.0, 0.0], [0.0, 1.0, 0.0], ForceKind.MEMBER, ForceDirection.COMPRESSION),
        ],
        active=True,
    )

    equilibrate_node(node)

    temp = node.get_temp_force()
    assert temp is not None
    assert temp.vector == [-1.0, -1.0, 0.0]


def test_extend_node_rule_adds_member_and_node():
    assembly = make_default_cantilever_scenario()
    assembly.state = GenerationState.GO
    load = assembly.node("2")
    load.type = NodeType.END
    rule = ExtendNodeRule(min_length=1.5, max_length=1.5)
    proposal = rule.propose(assembly, load, __import__("random").Random(0))[0]

    rule.apply(assembly, proposal, __import__("random").Random(0))

    assert len(assembly.nodes) == 4
    assert len(assembly.members) == 1


def test_create_node_does_not_invent_temporary_force_state():
    assembly = make_default_cantilever_scenario()
    assembly.state = GenerationState.GO
    load = assembly.node("2")
    rule = CreateNodeRule(min_length=0.5, max_length=0.5, min_angle=0.0, max_angle=0.0)
    proposal = rule.propose(assembly, load, __import__("random").Random(0))[0]
    rule.apply(assembly, proposal, __import__("random").Random(0))

    created = assembly.nodes[-1]
    assert created.type == NodeType.FLOAT
    assert created.forces == []
    assert created.get_temp_force() is None


def test_split_preserves_boundary_node_type_and_force():
    assembly = make_default_cantilever_scenario()
    assembly.state = GenerationState.GO
    support = assembly.node("0")
    reaction = [force.to_data() for force in support.forces if force.kind == ForceKind.REACTION]
    rule = SplitNodeRule(min_length=0.5, max_length=0.5, min_angle=0.2, max_angle=0.2)
    proposal = rule.propose(assembly, support, __import__("random").Random(0))[0]
    rule.apply(assembly, proposal, __import__("random").Random(0))

    assert support.type == NodeType.SUPPORT
    assert [force.to_data() for force in support.forces if force.kind == ForceKind.REACTION] == reaction


def test_default_scenario_initializes_gdgs_boundary_temp_forces():
    assembly = make_default_cantilever_scenario()

    assert assembly.state == GenerationState.START
    assert assembly.metadata["problem_id"] == "concurrent_three_force_smoke_v1"
    assert assembly.metadata["boundary_force_initialization"] == "gdgs_equilibrate_node_v1"
    assert assembly.node("0").coordinate == [0.0, -1.0, 0.0]
    assert assembly.node("1").coordinate == [0.0, 1.0, 0.0]
    assert assembly.node("2").coordinate == [3.0, 0.0, 0.0]
    reaction_a = [force for force in assembly.node("0").forces if force.kind == ForceKind.REACTION][0]
    reaction_b = [force for force in assembly.node("1").forces if force.kind == ForceKind.REACTION][0]
    assert reaction_a.vector == pytest.approx([7.5, 2.5, 0.0])
    assert reaction_b.vector == pytest.approx([-7.5, 2.5, 0.0])
    assert reaction_a.direction == ForceDirection.TENSION
    assert reaction_b.direction == ForceDirection.COMPRESSION
    assert assembly.node("0").get_temp_force().vector == pytest.approx([-7.5, -2.5, 0.0])
    assert assembly.node("1").get_temp_force().vector == pytest.approx([7.5, -2.5, 0.0])
    applied = [force for force in assembly.node("2").forces if force.kind == ForceKind.APPLIED][0]
    assert applied.vector == [0.0, -5.0, 0.0]
    assert assembly.node("2").get_temp_force().vector == [0.0, 5.0, 0.0]
    assert assembly.metadata["signed_reaction_magnitudes"]["0"] == pytest.approx(7.905694150420949)
    assert assembly.metadata["signed_reaction_magnitudes"]["1"] == pytest.approx(-7.905694150420949)
    assert assembly.metadata["reaction_directions_by_node"]["0"] == pytest.approx([0.9486832980505138, 0.31622776601683794, 0.0])
    assert assembly.metadata["reaction_directions_by_node"]["1"] == pytest.approx([0.9486832980505138, -0.31622776601683794, 0.0])
    assert assembly.metadata["benchmark_geometry"]["concurrency_point"] == [3.0, 0.0, 0.0]


def test_smoke_and_diversity_scenarios_have_distinct_reproducible_identities():
    smoke = make_concurrent_three_force_smoke_scenario()
    diversity_a = make_michell_diversity_cantilever_scenario()
    diversity_b = make_michell_diversity_cantilever_scenario()

    assert smoke.metadata["problem_id"] == "concurrent_three_force_smoke_v1"
    assert diversity_a.metadata["problem_id"] == "michell_diversity_cantilever_v1"
    assert diversity_a.to_data() == diversity_b.to_data()
    assert diversity_a.metadata["benchmark_geometry"] == smoke.metadata["benchmark_geometry"]


def test_gdgs_two_front_close_consumes_temp_forces_and_ends():
    support = Node(
        "support",
        [0.0, 0.0, 0.0],
        NodeType.SUPPORT,
        [
            Force([0.0, 0.0, 0.0], [0.0, 10.0, 0.0], ForceKind.REACTION),
            Force([0.0, 0.0, 0.0], [0.0, -10.0, 0.0], ForceKind.TEMPORARY),
        ],
        True,
    )
    load = Node(
        "load",
        [0.0, 1.0, 0.0],
        NodeType.LOAD,
        [
            Force([0.0, 1.0, 0.0], [0.0, -10.0, 0.0], ForceKind.APPLIED),
            Force([0.0, 1.0, 0.0], [0.0, 10.0, 0.0], ForceKind.TEMPORARY),
        ],
        True,
    )
    assembly = Assembly([support, load], [], BOUNDARY, state=GenerationState.GO)
    rule = CloseStructureRule(loopcount=-1)
    proposal = RuleProposal(rule.name, [support.node_id], {"active_count": 2}, rule.weight)

    rule.apply(assembly, proposal, __import__("random").Random(0))

    assert assembly.state == GenerationState.END
    assert len(assembly.members) == 1
    assert support.get_temp_force() is None
    assert load.get_temp_force() is None
    assert support.member_forces()[0].vector == [0.0, -10.0, 0.0]
    assert load.member_forces()[0].vector == [0.0, 10.0, 0.0]
    metrics = compute_kernel_metrics(assembly)
    assert metrics["benchmark_validity"]["duplicate_node_count"] == 0
    assert metrics["benchmark_validity"]["zero_length_member_count"] == 0


def test_michell_three_force_close_reuses_load_node_and_ends_validly():
    assembly = make_default_cantilever_scenario()
    assembly.state = GenerationState.GO
    rule = CloseStructureRule(loopcount=-1)
    proposal = rule.propose(assembly, assembly.node("2"), __import__("random").Random(0))[0]

    assert proposal.params["kind"] == "reuse_existing_hub"
    rule.apply(assembly, proposal, __import__("random").Random(0))

    assert assembly.state == GenerationState.END
    assert len(assembly.nodes) == 3
    assert len(assembly.members) == 2
    assert {tuple(sorted((member.start_node, member.end_node))) for member in assembly.members} == {
        ("0", "2"),
        ("1", "2"),
    }
    assert assembly.active_nodes() == []
    assert all(node.get_temp_force() is None for node in assembly.nodes)
    metrics = compute_kernel_metrics(assembly)
    assert metrics["final_residual_magnitude"] == 0.0
    assert metrics["support_connectivity"]["support_connected"] is True
    assert metrics["benchmark_validity"]["geometrically_valid"] is True
    assert metrics["benchmark_complete"] is True


def _active_temp_node(node_id, coordinate, vector):
    return Node(
        node_id,
        list(coordinate),
        NodeType.FLOAT,
        [Force(list(coordinate), list(vector), ForceKind.TEMPORARY)],
        True,
    )


@pytest.mark.parametrize("intersection", ([0.0, 0.0, 0.0], [1e-10, 0.0, 0.0]))
def test_connect_two_forces_rejects_coincident_intersection_without_mutation(intersection):
    node_a = _active_temp_node("a", [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    node_b = _active_temp_node("b", [0.0, 1.0, 0.0], [0.0, -1.0, 0.0])
    assembly = Assembly([node_a, node_b], [], BOUNDARY, state=GenerationState.GO)
    before = assembly.to_data()

    assert connect_two_forces(node_a, node_b, assembly, intersection) is False
    assert assembly.to_data() == before


def test_close_rule_does_not_propose_coincident_intersection():
    node_a = _active_temp_node("a", [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    node_b = _active_temp_node("b", [0.0, 1.0, 0.0], [0.0, -1.0, 0.0])
    node_c = _active_temp_node("c", [0.0, 2.0, 0.0], [1.0, 0.0, 0.0])
    assembly = Assembly([node_a, node_b, node_c], [], BOUNDARY, state=GenerationState.GO)
    rule = CloseStructureRule(loopcount=-1)

    assert rule.propose(assembly, node_a, __import__("random").Random(0)) == []
    assert assembly.state == GenerationState.GO


def test_gdgs_progressive_close_selects_nearest_intersection_and_returns_to_go():
    selected = _active_temp_node("0", [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    farther = _active_temp_node("1", [2.0, 1.0, 0.0], [0.0, -1.0, 0.0])
    nearer = _active_temp_node("2", [1.0, 2.0, 0.0], [0.0, -1.0, 0.0])
    assembly = Assembly([selected, farther, nearer], [], BOUNDARY, state=GenerationState.GO)
    for _ in range(5):
        assembly.add_history("PriorRule", [], {}, {})
    rule = CloseStructureRule()

    proposal = rule.propose(assembly, selected, __import__("random").Random(0))[0]

    assert proposal.target_node_ids == ["0", "2"]
    assert proposal.params["kind"] == "progressive_intersection"
    assert proposal.params["point"] == pytest.approx([1.0, 0.0, 0.0])

    rule.apply(assembly, proposal, __import__("random").Random(0))

    assert assembly.state == GenerationState.GO
    assert len(assembly.members) == 2
    assert len(assembly.active_nodes()) == 2
    assert assembly.history[-1].summary == {"progressive_closure_connection": True}


def test_gdgs_progressive_close_waits_for_loopcount():
    node_a = _active_temp_node("a", [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    node_b = _active_temp_node("b", [1.0, 1.0, 0.0], [0.0, -1.0, 0.0])
    node_c = _active_temp_node("c", [2.0, 2.0, 0.0], [0.0, -1.0, 0.0])
    assembly = Assembly([node_a, node_b, node_c], [], BOUNDARY, state=GenerationState.GO)
    rule = CloseStructureRule()

    assert rule.propose(assembly, node_a, __import__("random").Random(0)) == []


def test_connect_two_forces_rejects_self_connection_and_existing_edge():
    node_a = _active_temp_node("a", [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    node_b = _active_temp_node("b", [0.0, 1.0, 0.0], [0.0, -1.0, 0.0])
    assembly = Assembly([node_a, node_b], [], BOUNDARY, state=GenerationState.GO)
    before = assembly.to_data()

    assert connect_two_forces(node_a, node_a, assembly, [1.0, 0.0, 0.0]) is False
    assert assembly.to_data() == before

    assembly.members.append(Member("m0", "a", "b"))
    before = assembly.to_data()
    assert connect_two_forces(node_a, node_b, assembly, [1.0, 1.0, 0.0]) is False
    assert assembly.to_data() == before


def test_connection_segment_allows_crossing_existing_member():
    assembly = Assembly(
        [
            Node("a", [0.0, 0.0, 0.0], NodeType.FLOAT),
            Node("b", [2.0, 2.0, 0.0], NodeType.FLOAT),
            Node("c", [0.0, 2.0, 0.0], NodeType.FLOAT),
            Node("d", [2.0, 0.0, 0.0], NodeType.FLOAT),
        ],
        [Member("m0", "a", "b")],
        BOUNDARY,
    )

    assert segment_is_admissible(assembly, "c", "d", [0.0, 2.0, 0.0], [2.0, 0.0, 0.0]) is True


def test_connection_segment_rejects_collinear_overlap_with_shared_endpoint():
    assembly = Assembly(
        [
            Node("a", [0.0, 0.0, 0.0], NodeType.FLOAT),
            Node("b", [2.0, 0.0, 0.0], NodeType.FLOAT),
            Node("c", [3.0, 0.0, 0.0], NodeType.FLOAT),
        ],
        [Member("m0", "a", "b")],
        BOUNDARY,
    )

    assert segment_is_admissible(assembly, "a", "c", [0.0, 0.0, 0.0], [3.0, 0.0, 0.0]) is False


def test_kernel_does_not_mark_unresolved_dead_end_as_end():
    class StartOnlyRule:
        name = "StartGeneration"

        def propose(self, assembly, node, rng):
            if assembly.state == GenerationState.START:
                return [RuleProposal(self.name, [], {}, 1)]
            return []

        def apply(self, assembly, proposal, rng):
            assembly.state = GenerationState.GO
            return assembly

    assembly = make_default_cantilever_scenario()
    final, trace = VectorGSKernelV1(rules=[StartOnlyRule()], seed=0).run(assembly, max_steps=4)

    assert [step["rule"] for step in trace] == ["StartGeneration"]
    assert final.state == GenerationState.GO
    assert final.active_nodes()


def test_run_artifact_records_budget_termination_and_benchmark_metadata(tmp_path):
    assembly = make_default_cantilever_scenario()
    out_path = export_run(
        tmp_path / "seed_0",
        assembly,
        [],
        assembly.metadata["scenario_name"],
        0,
        problem_id="michell_three_point_cantilever_v1",
        policy_id="rule_weighted_random_v1",
        step_budget=12,
        termination_reason="state_end",
        final_metrics=compute_kernel_metrics(assembly),
    )

    payload = json.loads(out_path.read_text())
    assert payload["problem_id"] == "michell_three_point_cantilever_v1"
    assert payload["step_budget"] == 12
    assert payload["termination_reason"] == "state_end"
    assert payload["assembly"]["metadata"]["benchmark_geometry"]["concurrency_point"] == [3.0, 0.0, 0.0]
    assert payload["assembly"]["metadata"]["signed_reaction_magnitudes"]["1"] < 0.0


def test_kernel_smoke_run_generates_nontrivial_structure():
    assembly = make_default_cantilever_scenario()
    kernel = VectorGSKernelV1(seed=0)
    final_assembly, trace = kernel.run(assembly, max_steps=8)

    assert trace
    assert len(final_assembly.nodes) > 3 or len(final_assembly.members) >= 1
    assert any(step["rule"] != "StartGeneration" for step in trace)
    assert trace[0]["assembly_before"]["state"] == GenerationState.START
    assert trace[0]["assembly_after"]["state"] == GenerationState.GO
    assert trace[-1]["assembly_after"] == final_assembly.to_data()


def test_kernel_policy_controls_proposal_selection_mode():
    proposals = [
        RuleProposal("HeavyRule", ["1"], {}, 30),
        RuleProposal("LightRule", ["2"], {}, 1),
    ]

    weighted_kernel = VectorGSKernelV1(seed=0, policy_id="rule_weighted_random_v1")
    uniform_kernel = VectorGSKernelV1(seed=0, policy_id="rule_uniform_random_v1")

    weighted_pick = weighted_kernel._select_proposal(proposals)
    uniform_pick = uniform_kernel._select_proposal(proposals)

    assert weighted_pick.rule_name == "HeavyRule"
    assert uniform_pick.rule_name == "LightRule"


def test_uniform_policy_assigns_equal_probability_and_ignores_rule_weights():
    proposals = [
        RuleProposal("CloseStructure", ["0"], {}, 1000),
        RuleProposal("SplitNode", ["1"], {}, 1),
        RuleProposal("ExtendNode", ["2"], {}, 25),
    ]
    kernel = VectorGSKernelV1(seed=4, policy_id="rule_uniform_random_v1")

    assert kernel._proposal_probabilities(proposals) == pytest.approx([1.0 / 3.0] * 3)

    changed_weights = [
        RuleProposal(proposal.rule_name, proposal.target_node_ids, proposal.params, 9999 - index)
        for index, proposal in enumerate(proposals)
    ]
    first = VectorGSKernelV1(seed=9, policy_id="rule_uniform_random_v1")._select_proposal(proposals)
    second = VectorGSKernelV1(seed=9, policy_id="rule_uniform_random_v1")._select_proposal(changed_weights)
    assert first.rule_name == second.rule_name


def test_uniform_policy_exposes_proposals_from_every_active_node():
    class NodeRule:
        name = "NodeRule"

        def propose(self, assembly, node, rng):
            if node is None:
                return []
            return [RuleProposal(self.name, [node.node_id], {}, 1)]

    class EndRule:
        name = "EndGeneration"

        def propose(self, assembly, node, rng):
            return []

    assembly = make_michell_diversity_cantilever_scenario()
    assembly.state = GenerationState.GO
    kernel = VectorGSKernelV1(
        rules=[EndRule(), NodeRule(), EndRule()],
        seed=0,
        policy_id="rule_uniform_random_v1",
    )

    proposals = kernel._all_proposals(assembly)

    assert {proposal.target_node_ids[0] for proposal in proposals} == {"0", "1", "2"}


def test_kernel_benchmark_completion_requires_support_connectivity():
    assembly = make_default_cantilever_scenario()
    for node in assembly.nodes:
        node.remove_temp_forces()
        node.active = False

    metrics = compute_kernel_metrics(assembly)

    assert metrics["equilibrium_reached"] is True
    assert metrics["support_connectivity"]["support_connected"] is False
    assert metrics["benchmark_validity"]["geometrically_valid"] is True
    assert metrics["benchmark_complete"] is False


def test_michell_three_point_cantilever_reports_closed_boundary_force_triangle():
    assembly = make_default_cantilever_scenario()

    metrics = compute_kernel_metrics(assembly)
    polygon = metrics["boundary_force_polygon"]

    assert polygon["force_convention"] == "tail_to_head_vectors_head_to_tail_polygon"
    assert polygon["total_applied_force"] == [0.0, -5.0, 0.0]
    assert polygon["total_reaction_force"] == pytest.approx([0.0, 5.0, 0.0])
    assert polygon["polygon_residual"] == [0.0, 0.0, 0.0]
    assert polygon["polygon_residual_magnitude"] == 0.0
    assert polygon["externally_balanced"] is True
    assert [reaction["node_id"] for reaction in polygon["solved_reactions"]] == ["0", "1"]
    assert [reaction["vector"] for reaction in polygon["solved_reactions"]] == [
        pytest.approx([7.5, 2.5, 0.0]),
        pytest.approx([-7.5, 2.5, 0.0]),
    ]


def test_kernel_benchmark_completion_requires_geometric_validity():
    support = Node("support", [0.0, 0.0, 0.0], NodeType.SUPPORT, active=False)
    load = Node("load", [1.0, 1.0, 0.0], NodeType.LOAD, forces=[], active=False)
    far = Node("far", [10.0, 1.0, 0.0], NodeType.FLOAT, forces=[], active=False)
    assembly = make_default_cantilever_scenario()
    assembly.nodes = [support, load, far]
    assembly.members = [
        Member("m0", "support", "load"),
        Member("m1", "load", "far"),
    ]
    assembly.boundary = BOUNDARY

    metrics = compute_kernel_metrics(assembly)

    assert metrics["equilibrium_reached"] is True
    assert metrics["support_connectivity"]["support_connected"] is True
    assert metrics["benchmark_validity"]["geometrically_valid"] is False
    assert metrics["benchmark_validity"]["out_of_bounds_node_count"] == 1
    assert metrics["benchmark_validity"]["invalid_reasons"] == ["nodes_outside_bounds"]
    assert metrics["benchmark_complete"] is False


def test_kernel_validity_reports_crossing_members():
    assembly = make_default_cantilever_scenario()
    assembly.boundary = BOUNDARY
    assembly.nodes = [
        Node("a", [0.0, 0.0, 0.0], NodeType.SUPPORT, active=False),
        Node("b", [4.0, 4.0, 0.0], NodeType.LOAD, active=False),
        Node("c", [0.0, 4.0, 0.0], NodeType.FLOAT, active=False),
        Node("d", [4.0, 0.0, 0.0], NodeType.FLOAT, active=False),
    ]
    assembly.members = [
        Member("m0", "a", "b"),
        Member("m1", "c", "d"),
    ]

    metrics = compute_kernel_metrics(assembly)

    assert metrics["benchmark_validity"]["crossing_member_count"] == 1
    assert metrics["benchmark_validity"]["invalid_reasons"] == ["crossing_members"]
    assert metrics["benchmark_complete"] is False
