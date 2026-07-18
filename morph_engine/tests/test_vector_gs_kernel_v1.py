import json
import pytest

from morph_engine.vector_gs_kernel_v1 import VectorGSKernelV1
from morph_engine.vector_gs_kernel_v1.engine import GDGS_NODE_RULE_UNIFORM_POLICY_ID
from morph_engine.vector_gs_kernel_v1.engine import INCOMPLETE_PHASE
from morph_engine.vector_gs_kernel_v1.engine import VERIFY_PHASE
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
from morph_engine.vector_gs_kernel_v1.operators import connect_two_forces_at_existing_hub
from morph_engine.vector_gs_kernel_v1.operators import closure_ray_candidate
from morph_engine.vector_gs_kernel_v1.operators import equilibrate_node
from morph_engine.vector_gs_kernel_v1.operators import segment_is_admissible
from morph_engine.vector_gs_kernel_v1.operators import structural_completion_reason
from morph_engine.vector_gs_kernel_v1.rules import RuleProposal
from morph_engine.vector_gs_kernel_v1.rules import RuleParameterConfiguration
from morph_engine.vector_gs_kernel_v1.rules import ConnectTwoNodesRule
from morph_engine.vector_gs_kernel_v1.rules import CreateNodeRule
from morph_engine.vector_gs_kernel_v1.rules import ExtendNodeRule
from morph_engine.vector_gs_kernel_v1.rules import StartGenerationRule
from morph_engine.vector_gs_kernel_v1.rules import ExtendAndConnectTwoNodesRule
from morph_engine.vector_gs_kernel_v1.rules import CloseStructureRule
from morph_engine.vector_gs_kernel_v1.rules import CONNECTIVITY_FAMILY
from morph_engine.vector_gs_kernel_v1.rules import EndGenerationRule
from morph_engine.vector_gs_kernel_v1.rules import SplitNodeRule
from morph_engine.vector_gs_kernel_v1.scenarios import make_concurrent_three_force_smoke_scenario
from morph_engine.vector_gs_kernel_v1.scenarios import make_michell_diversity_cantilever_scenario
from morph_engine.vector_gs_kernel_v1.scenarios import ReactionAngleConfiguration


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


def test_reaction_angle_configuration_preserves_external_equilibrium_and_provenance():
    configuration = ReactionAngleConfiguration(
        configuration_id="test_27deg",
        lower_support_angle_degrees=27.0,
    )
    assembly = make_default_cantilever_scenario(configuration)
    metrics = compute_kernel_metrics(assembly)

    assert metrics["boundary_force_polygon"]["externally_balanced"] is True
    assert assembly.metadata["reaction_angle_configuration"]["configuration_id"] == "test_27deg"
    assert assembly.metadata["benchmark_geometry"]["concurrency_point"][0] == 3.0
    assert assembly.metadata["benchmark_geometry"]["concurrency_point"] != [3.0, 0.0, 0.0]


def test_smoke_and_diversity_scenarios_are_geometrically_distinct_and_reproducible():
    smoke = make_concurrent_three_force_smoke_scenario()
    diversity_a = make_michell_diversity_cantilever_scenario()
    diversity_b = make_michell_diversity_cantilever_scenario()

    assert (
        smoke.metadata["benchmark_geometry"]["concurrency_point"]
        != diversity_a.metadata["benchmark_geometry"]["concurrency_point"]
    )
    assert diversity_a.to_data() == diversity_b.to_data()


@pytest.mark.parametrize(
    "direction,expected_class,expected_signed",
    [
        (ForceDirection.TENSION, "tension", 2.0),
        (ForceDirection.COMPRESSION, "compression", -2.0),
    ],
)
def test_member_serialization_exposes_signed_axial_class(direction, expected_class, expected_signed):
    member = Member(
        "m0",
        "a",
        "b",
        Force(
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            ForceKind.MEMBER,
            direction=direction,
            related_member="m0",
            metadata={"semantic_origin": "phase_0b_test"},
        ),
    )

    payload = member.to_data()

    assert payload["force_class"] == expected_class
    assert payload["force_magnitude"] == 2.0
    assert payload["signed_axial_force"] == expected_signed
    assert payload["classification_source"] == "phase_0b_test"


def test_member_force_diagnostics_validate_equal_and_opposite_endpoint_records():
    direction = ForceDirection.TENSION
    node_a = Node(
        "a",
        [0.0, 0.0, 0.0],
        NodeType.FLOAT,
        [Force([0.0, 0.0, 0.0], [2.0, 0.0, 0.0], ForceKind.MEMBER, direction, "m0")],
        False,
    )
    node_b = Node(
        "b",
        [4.0, 0.0, 0.0],
        NodeType.FLOAT,
        [Force([4.0, 0.0, 0.0], [-2.0, 0.0, 0.0], ForceKind.MEMBER, direction, "m0")],
        False,
    )
    member_force = Force(
        [0.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        ForceKind.MEMBER,
        direction,
        "m0",
        {"classification_source": "test_fixture"},
    )
    assembly = Assembly([node_a, node_b], [Member("m0", "a", "b", member_force)], BOUNDARY)

    diagnostics = compute_kernel_metrics(assembly)["member_force_diagnostics"]

    assert diagnostics["sign_convention"] == "tension_positive_compression_negative"
    assert diagnostics["classification_is_policy_input"] is False
    assert diagnostics["tension_count"] == 1
    assert diagnostics["compression_count"] == 0
    assert diagnostics["all_classifications_valid"] is True
    assert diagnostics["members"][0]["classification_valid"] is True
    assert diagnostics["members"][0]["signed_axial_force"] == 2.0


def test_member_force_diagnostics_report_endpoint_class_mismatch():
    node_a = Node(
        "a",
        [0.0, 0.0, 0.0],
        NodeType.FLOAT,
        [Force([0.0, 0.0, 0.0], [1.0, 0.0, 0.0], ForceKind.MEMBER, ForceDirection.TENSION, "m0")],
        False,
    )
    node_b = Node(
        "b",
        [1.0, 0.0, 0.0],
        NodeType.FLOAT,
        [Force([1.0, 0.0, 0.0], [-1.0, 0.0, 0.0], ForceKind.MEMBER, ForceDirection.COMPRESSION, "m0")],
        False,
    )
    member = Member(
        "m0",
        "a",
        "b",
        Force([0.0, 0.0, 0.0], [1.0, 0.0, 0.0], ForceKind.MEMBER, ForceDirection.TENSION, "m0"),
    )

    diagnostics = compute_kernel_metrics(Assembly([node_a, node_b], [member], BOUNDARY))[
        "member_force_diagnostics"
    ]

    assert diagnostics["all_classifications_valid"] is False
    assert diagnostics["invalid_classification_count"] == 1
    assert "endpoint_class_mismatch" in diagnostics["members"][0]["validation_reasons"]


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


def test_rule_parameter_configuration_is_recorded_and_uses_growth_counter():
    configuration = RuleParameterConfiguration(
        configuration_id="bounded_rotation_test",
        create_min_rotation=-0.25,
        create_max_rotation=0.25,
        create_growth_step_limit=4,
    )
    assembly = make_default_cantilever_scenario()
    assembly.state = GenerationState.GO
    assembly.metadata["growth_step_count"] = 3
    rule = CreateNodeRule(cutoff=4)

    assert rule.applicable_to(assembly, assembly.node("0")) is True

    final, _ = VectorGSKernelV1(
        seed=0,
        growth_limit=1,
        rule_parameter_configuration=configuration,
    ).run(make_default_cantilever_scenario(), max_steps=10)
    assert (
        final.metadata["rule_parameter_configuration"]["configuration_id"]
        == "bounded_rotation_test"
    )


def test_custom_rules_have_explicit_provenance_and_reject_parameter_claims():
    custom_rule = StartGenerationRule()
    kernel = VectorGSKernelV1(rules=[custom_rule], seed=0)
    final, _ = kernel.run(make_default_cantilever_scenario(), max_steps=1)

    assert final.metadata["rule_source"] == "custom_rules"
    assert final.metadata["rule_parameter_configuration"] is None
    with pytest.raises(ValueError, match="custom rules"):
        VectorGSKernelV1(
            rules=[custom_rule],
            rule_parameter_configuration=RuleParameterConfiguration(),
        )


def test_extend_node_does_not_propose_out_of_bounds_member():
    assembly = make_default_cantilever_scenario()
    assembly.state = GenerationState.GO
    support = assembly.node("0")
    support.type = NodeType.END
    rule = ExtendNodeRule(min_length=2.0, max_length=2.0)

    assert rule.propose(assembly, support, __import__("random").Random(0)) == []


def test_create_node_propagates_temporary_force_state_and_member():
    assembly = make_default_cantilever_scenario()
    assembly.state = GenerationState.GO
    load = assembly.node("2")
    rule = CreateNodeRule(
        min_length=0.5,
        max_length=0.5,
        min_angle=0.0,
        max_angle=0.0,
        min_rotation=0.0,
        max_rotation=0.0,
    )
    proposal = rule.propose(assembly, load, __import__("random").Random(0))[0]
    rule.apply(assembly, proposal, __import__("random").Random(0))

    created = assembly.nodes[-1]
    assert created.type == NodeType.END
    assert len(assembly.members) == 1
    assert len(created.member_forces()) == 1
    assert created.get_temp_force() is not None
    assert created.member_forces()[0].vector == pytest.approx([0.0, -5.0, 0.0])
    assert created.get_temp_force().vector == pytest.approx([0.0, 5.0, 0.0])
    assert ExtendNodeRule(min_length=0.25, max_length=0.25).applicable_to(assembly, created)
    assert assembly.history[-1].params["rotation"] == 0.0


def test_create_node_does_not_propose_out_of_bounds_node():
    assembly = make_default_cantilever_scenario()
    assembly.state = GenerationState.GO
    support = assembly.node("0")
    rule = CreateNodeRule(
        min_length=2.0,
        max_length=2.0,
        min_angle=0.0,
        max_angle=0.0,
        min_rotation=0.0,
        max_rotation=0.0,
    )

    before = assembly.to_data()
    assert rule.propose(assembly, support, __import__("random").Random(0)) == []
    assert assembly.to_data() == before


def test_create_node_rotation_controls_collinear_member_direction():
    assembly = make_default_cantilever_scenario()
    assembly.state = GenerationState.GO
    load = assembly.node("2")
    rule = CreateNodeRule(
        min_length=0.5,
        max_length=0.5,
        min_angle=0.0,
        max_angle=0.0,
        min_rotation=1.5707963267948966,
        max_rotation=1.5707963267948966,
    )
    proposal = rule.propose(assembly, load, __import__("random").Random(0))[0]
    rule.apply(assembly, proposal, __import__("random").Random(0))

    created = assembly.nodes[-1]
    assert created.coordinate == pytest.approx([2.5, 0.0, 0.0])
    assert assembly.members[-1].force.vector == pytest.approx([-5.0, 0.0, 0.0])
    assert created.member_forces()[0].vector == pytest.approx([5.0, 0.0, 0.0])
    assert created.get_temp_force().vector == pytest.approx([-5.0, 0.0, 0.0])


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
    assert len(assembly.nodes) == 5
    assert len(assembly.members) == 2
    assert support.get_temp_force() is None
    assert len(support.member_forces()) == 2
    assert assembly.history[-1].target_node_ids == ["0"]


def test_split_does_not_propose_out_of_bounds_branches():
    assembly = make_default_cantilever_scenario()
    assembly.state = GenerationState.GO
    support = assembly.node("0")
    rule = SplitNodeRule(min_length=2.0, max_length=2.0, min_angle=0.2, max_angle=0.2)

    assert rule.propose(assembly, support, __import__("random").Random(0)) == []


def test_extend_and_connect_targets_two_fronts_and_creates_corner():
    node_a = _active_temp_node("a", [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    node_b = _active_temp_node("b", [1.0, 1.0, 0.0], [0.0, -1.0, 0.0])
    assembly = Assembly([node_a, node_b], [], BOUNDARY, state=GenerationState.GO)
    rule = ExtendAndConnectTwoNodesRule(radius=10.0)

    proposal = rule.propose(assembly, node_a, __import__("random").Random(0))[0]

    assert proposal.target_node_ids == ["a", "b"]
    assert proposal.params["kind"] == "projection"
    assert proposal.params["point"] == pytest.approx([1.0, 0.0, 0.0])

    rule.apply(assembly, proposal, __import__("random").Random(0))

    assert len(assembly.nodes) == 3
    assert len(assembly.members) == 2
    assert node_a.active is False
    assert node_b.active is False
    corner = assembly.nodes[-1]
    assert corner.type == NodeType.CORNER
    assert corner.coordinate == pytest.approx([1.0, 0.0, 0.0])
    assert corner.active is True
    assert assembly.history[-1].target_node_ids == ["a", "b"]
    assert assembly.history[-1].summary == {"new_projection_node": corner.node_id}


def test_extend_and_connect_does_not_propose_out_of_bounds_intersection():
    node_a = _active_temp_node("a", [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    node_b = _active_temp_node("b", [7.0, 1.0, 0.0], [0.0, -1.0, 0.0])
    assembly = Assembly([node_a, node_b], [], BOUNDARY, state=GenerationState.GO)
    rule = ExtendAndConnectTwoNodesRule(radius=10.0)

    assert rule.propose(assembly, node_a, __import__("random").Random(0)) == []


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
    assert diversity_a.metadata["benchmark_geometry"] != smoke.metadata["benchmark_geometry"]


def test_gdgs_two_front_close_consumes_temp_forces_and_remains_in_close():
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
    assembly = Assembly([support, load], [], BOUNDARY, state=GenerationState.CLOSE)
    rule = CloseStructureRule(loopcount=-1)
    proposal = RuleProposal(rule.name, [support.node_id], {"active_count": 2}, rule.weight)

    rule.apply(assembly, proposal, __import__("random").Random(0))

    assert assembly.state == GenerationState.CLOSE
    assert len(assembly.members) == 1
    assert support.get_temp_force() is None
    assert load.get_temp_force() is None
    assert support.member_forces()[0].vector == [0.0, -10.0, 0.0]
    assert load.member_forces()[0].vector == [0.0, 10.0, 0.0]
    metrics = compute_kernel_metrics(assembly)
    assert metrics["benchmark_validity"]["duplicate_node_count"] == 0
    assert metrics["benchmark_validity"]["zero_length_member_count"] == 0


def test_progressive_closure_can_reuse_existing_third_node():
    node_a = _active_temp_node("a", [0.0, 0.0, 0.0], [1.0, 1.0, 0.0])
    node_b = _active_temp_node("b", [2.0, 0.0, 0.0], [-1.0, 1.0, 0.0])
    hub = Node("hub", [1.0, 1.0, 0.0], NodeType.FLOAT, active=False)
    assembly = Assembly(
        [node_a, node_b, hub],
        [],
        {"min": [-1.0, -1.0, 0.0], "max": [3.0, 2.0, 0.0]},
        state=GenerationState.CLOSE,
    )

    candidate = closure_ray_candidate(node_a, node_b, assembly, 1, 1)

    assert candidate["rejection_reason"] is None
    assert candidate["existing_hub_node"] == "hub"
    assert connect_two_forces_at_existing_hub(
        node_a, node_b, hub, assembly, 1, 1
    )
    assert not node_a.active
    assert not node_b.active
    assert hub.active
    assert len(assembly.members) == 2
    assert {member.end_node for member in assembly.members} == {"hub"}


def test_existing_hub_closure_preserves_forces_and_endpoint_equilibrium():
    node_a = Node(
        "a",
        [0.0, 0.0, 0.0],
        NodeType.FLOAT,
        forces=[
            Force([0.0, 0.0, 0.0], [-1.0, -1.0, 0.0], ForceKind.APPLIED),
            Force([0.0, 0.0, 0.0], [1.0, 1.0, 0.0], ForceKind.TEMPORARY),
        ],
        active=True,
    )
    node_b = Node(
        "b",
        [2.0, 0.0, 0.0],
        NodeType.FLOAT,
        forces=[
            Force([2.0, 0.0, 0.0], [1.0, -1.0, 0.0], ForceKind.APPLIED),
            Force([2.0, 0.0, 0.0], [-1.0, 1.0, 0.0], ForceKind.TEMPORARY),
        ],
        active=True,
    )
    hub = Node(
        "hub",
        [1.0, 1.0, 0.0],
        NodeType.LOAD,
        forces=[
            Force([1.0, 1.0, 0.0], [0.0, 4.0, 0.0], ForceKind.APPLIED),
            Force([1.0, 1.0, 0.0], [0.0, -1.0, 0.0], ForceKind.REACTION),
            Force(
                [1.0, 1.0, 0.0],
                [0.0, -1.0, 0.0],
                ForceKind.MEMBER,
                related_member="m0",
            ),
            Force([1.0, 1.0, 0.0], [0.0, -2.0, 0.0], ForceKind.TEMPORARY),
        ],
        active=True,
    )
    existing = Node("existing", [1.0, 2.0, 0.0], NodeType.FLOAT, active=False)
    assembly = Assembly(
        [node_a, node_b, hub, existing],
        [Member("m0", "hub", "existing", force=hub.member_forces()[0])],
        {"min": [-1.0, -1.0, 0.0], "max": [3.0, 3.0, 0.0]},
        state=GenerationState.CLOSE,
    )
    preserved = [
        (force.kind, list(force.vector), force.related_member)
        for force in hub.forces
        if force.kind != ForceKind.TEMPORARY
    ]

    assert connect_two_forces_at_existing_hub(
        node_a, node_b, hub, assembly, 1, 1
    )

    after_non_temporary = [
        (force.kind, list(force.vector), force.related_member)
        for force in hub.forces
        if force.kind != ForceKind.TEMPORARY
    ]
    assert all(force_record in after_non_temporary for force_record in preserved)
    assert hub.get_temp_force() is None
    assert hub.active is False
    for node in (node_a, node_b, hub):
        assert node.local_resultant() == pytest.approx([0.0, 0.0, 0.0])
    for member in assembly.members[1:]:
        start_force = next(
            force
            for force in assembly.node(member.start_node).member_forces()
            if force.related_member == member.member_id
        )
        end_force = next(
            force
            for force in assembly.node(member.end_node).member_forces()
            if force.related_member == member.member_id
        )
        assert end_force.vector == pytest.approx(
            [-component for component in start_force.vector]
        )


def test_michell_three_force_close_reuses_load_node_and_awaits_verification():
    assembly = make_default_cantilever_scenario()
    assembly.state = GenerationState.CLOSE
    rule = CloseStructureRule(loopcount=-1)
    proposal = rule.propose(assembly, assembly.node("2"), __import__("random").Random(0))[0]

    assert proposal.params["kind"] == "reuse_existing_hub"
    rule.apply(assembly, proposal, __import__("random").Random(0))

    assert assembly.state == GenerationState.CLOSE
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
    assembly = Assembly([node_a, node_b, node_c], [], BOUNDARY, state=GenerationState.CLOSE)
    rule = CloseStructureRule(loopcount=-1)

    assert rule.propose(assembly, node_a, __import__("random").Random(0)) == []
    assert assembly.state == GenerationState.CLOSE


def test_gdgs_progressive_close_selects_nearest_intersection_and_remains_in_close():
    selected = _active_temp_node("0", [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    farther = _active_temp_node("1", [2.0, 1.0, 0.0], [0.0, -1.0, 0.0])
    nearer = _active_temp_node("2", [1.0, 2.0, 0.0], [0.0, -1.0, 0.0])
    assembly = Assembly([selected, farther, nearer], [], BOUNDARY, state=GenerationState.CLOSE)
    for _ in range(5):
        assembly.add_history("PriorRule", [], {}, {})
    rule = CloseStructureRule()

    proposal = rule.propose(assembly, selected, __import__("random").Random(0))[0]

    assert proposal.target_node_ids == ["0", "2"]
    assert proposal.params["kind"] == "progressive_intersection"
    assert proposal.params["point"] == pytest.approx([1.0, 0.0, 0.0])
    assert proposal.params["ray_combination"] == [1, 1]
    assert len(proposal.params["candidate_intersections"]) == 8

    rule.apply(assembly, proposal, __import__("random").Random(0))

    assert assembly.state == GenerationState.CLOSE
    assert len(assembly.members) == 2
    assert len(assembly.active_nodes()) == 2
    assert assembly.history[-1].summary == {"progressive_closure_connection": True}


def test_rule6_prefers_first_valid_gdgs_ray_combination_over_global_distance():
    selected = _active_temp_node("0", [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    farther_positive = _active_temp_node("1", [4.0, 1.0, 0.0], [0.0, -1.0, 0.0])
    nearer_opposite = _active_temp_node("2", [1.0, -1.0, 0.0], [0.0, -1.0, 0.0])
    assembly = Assembly([selected, farther_positive, nearer_opposite], [], BOUNDARY, state=GenerationState.CLOSE)
    for _ in range(5):
        assembly.add_history("PriorRule", [], {}, {})

    proposal = CloseStructureRule().propose(assembly, selected, __import__("random").Random(0))[0]

    assert proposal.target_node_ids == ["0", "1"]
    assert proposal.params["ray_combination"] == [1, 1]
    assert proposal.params["point"] == pytest.approx([4.0, 0.0, 0.0])
    nearer_candidate = next(
        candidate
        for candidate in proposal.params["candidate_intersections"]
        if candidate["target_node"] == "2"
        and candidate["source_ray_sign"] == 1
        and candidate["target_ray_sign"] == -1
    )
    assert nearer_candidate["rejection_reason"] is None
    assert nearer_candidate["distance_measure"] == pytest.approx(1.0)


@pytest.mark.parametrize(
    "source_coordinate,target_coordinate,source_vector,target_vector,expected_signs",
    [
        ([0.0, 0.0, 0.0], [1.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, -1.0, 0.0], (1, 1)),
        ([0.0, 0.0, 0.0], [1.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, -1.0, 0.0], (1, -1)),
        ([0.0, 0.0, 0.0], [-1.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, -1.0, 0.0], (-1, 1)),
        ([0.0, 0.0, 0.0], [-1.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, -1.0, 0.0], (-1, -1)),
    ],
)
def test_rule6_explicit_ray_combinations(
    source_coordinate,
    target_coordinate,
    source_vector,
    target_vector,
    expected_signs,
):
    source = _active_temp_node("source", source_coordinate, source_vector)
    target = _active_temp_node("target", target_coordinate, target_vector)
    assembly = Assembly([source, target], [], {"min": [-2.0, -2.0, 0.0], "max": [2.0, 2.0, 0.0]}, state=GenerationState.GO)

    candidate = closure_ray_candidate(source, target, assembly, *expected_signs)

    assert candidate["rejection_reason"] is None
    assert candidate["source_ray_sign"] == expected_signs[0]
    assert candidate["target_ray_sign"] == expected_signs[1]
    assert candidate["source_ray_parameter"] >= 0.0
    assert candidate["target_ray_parameter"] >= 0.0


def test_rule6_opposite_ray_keeps_force_vector_and_classifies_compression():
    source = _active_temp_node("source", [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    target = _active_temp_node("target", [-1.0, 1.0, 0.0], [0.0, -1.0, 0.0])
    third = _active_temp_node("third", [1.0, 2.0, 0.0], [1.0, 0.0, 0.0])
    assembly = Assembly([source, target, third], [], {"min": [-2.0, -2.0, 0.0], "max": [2.0, 3.0, 0.0]}, state=GenerationState.CLOSE)
    for _ in range(5):
        assembly.add_history("PriorRule", [], {}, {})
    rule = CloseStructureRule()
    proposal = rule.propose(assembly, source, __import__("random").Random(0))[0]

    assert proposal.params["ray_combination"] == [-1, 1]
    original_vector = list(source.get_temp_force().vector)
    rule.apply(assembly, proposal, __import__("random").Random(0))

    assert source.member_forces()[-1].vector == original_vector
    assert source.member_forces()[-1].direction == ForceDirection.COMPRESSION


def test_rule6_rejects_wrong_ray_sign_with_explicit_reason():
    source = _active_temp_node("source", [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    target = _active_temp_node("target", [1.0, 1.0, 0.0], [0.0, -1.0, 0.0])
    assembly = Assembly([source, target], [], BOUNDARY, state=GenerationState.GO)

    candidate = closure_ray_candidate(source, target, assembly, -1, 1)

    assert candidate["rejection_reason"] == "negative_ray_parameter"


def test_rule6_can_reduce_active_fronts_repeatedly():
    node_a = _active_temp_node("a", [0.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    node_b = _active_temp_node("b", [1.0, 1.0, 0.0], [0.0, -1.0, 0.0])
    node_c = _active_temp_node("c", [2.0, 1.0, 0.0], [0.0, -1.0, 0.0])
    node_d = _active_temp_node("d", [3.0, 0.0, 0.0], [-1.0, 0.0, 0.0])
    assembly = Assembly([node_a, node_b, node_c, node_d], [], BOUNDARY, state=GenerationState.CLOSE)
    for _ in range(5):
        assembly.add_history("PriorRule", [], {}, {})
    rule = CloseStructureRule()

    first = rule.propose(assembly, node_a, __import__("random").Random(0))[0]
    rule.apply(assembly, first, __import__("random").Random(0))
    assert len(assembly.active_nodes()) == 3

    corner = assembly.nodes[-1]
    second = rule.propose(assembly, corner, __import__("random").Random(0))[0]
    rule.apply(assembly, second, __import__("random").Random(0))
    assert len(assembly.active_nodes()) == 2


def test_close_structure_is_not_admissible_during_grow():
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


def test_connection_segment_rejects_crossing_existing_member_without_mutation():
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
    before = assembly.to_data()

    assert segment_is_admissible(assembly, "c", "d", [0.0, 2.0, 0.0], [2.0, 0.0, 0.0]) is False
    assert assembly.to_data() == before


def test_connect_rule_filters_crossing_proposal_without_canonical_state_mutation():
    node_c = _active_temp_node("c", [0.0, 2.0, 0.0], [1.0, -1.0, 0.0])
    node_d = _active_temp_node("d", [2.0, 0.0, 0.0], [-1.0, 1.0, 0.0])
    assembly = Assembly(
        [
            Node("a", [0.0, 0.0, 0.0], NodeType.FLOAT),
            Node("b", [2.0, 2.0, 0.0], NodeType.FLOAT),
            node_c,
            node_d,
        ],
        [Member("m0", "a", "b")],
        BOUNDARY,
        state=GenerationState.GO,
    )
    before = assembly.to_data()

    proposals = ConnectTwoNodesRule(radius=10.0).propose(
        assembly,
        node_c,
        __import__("random").Random(0),
    )

    assert proposals == []
    assert assembly.to_data() == before


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

    assert [step["rule"] for step in trace] == ["StartGeneration", None]
    assert final.state == INCOMPLETE_PHASE
    assert final.active_nodes()
    assert final.metadata["termination_reason"] == "no_applicable_growth_rules"


def test_end_generation_rejects_unresolved_force_fronts():
    assembly = make_default_cantilever_scenario()
    assembly.state = VERIFY_PHASE
    rule = EndGenerationRule(max_steps=0)
    proposal = rule.propose(assembly, None, __import__("random").Random(0))[0]

    rule.apply(assembly, proposal, __import__("random").Random(0))

    assert assembly.state == INCOMPLETE_PHASE
    assert assembly.metadata["termination_reason"] == "unresolved_force_fronts"


def test_structural_completion_rejects_member_endpoint_force_mismatch():
    assembly = make_default_cantilever_scenario()
    assembly.state = GenerationState.CLOSE
    rule = CloseStructureRule(loopcount=-1)
    proposal = rule.propose(assembly, assembly.node("2"), __import__("random").Random(0))[0]
    rule.apply(assembly, proposal, __import__("random").Random(0))
    assert structural_completion_reason(assembly) is None

    assembly.node("0").member_forces()[0].vector[0] += 1.0

    assert structural_completion_reason(assembly) == "no_valid_closure"


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
    assert all("selected_active_node" in step for step in trace)
    assert all("eligible_active_nodes" in step for step in trace)
    assert all("applicable_rule_families" in step for step in trace)
    assert all("rule_family_weights" in step for step in trace)
    assert all("selected_rule_family" in step for step in trace)
    assert all("active_front_count_before" in step for step in trace)
    assert all("active_front_count_after" in step for step in trace)


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
        family = CONNECTIVITY_FAMILY

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


def test_gdgs_policy_selects_uniform_active_node_before_rule_family():
    class StartRule:
        name = "StartGeneration"
        weight = 1

    class NodeRule:
        name = "NodeRule"
        weight = 1
        family = CONNECTIVITY_FAMILY

        def applicable_to(self, assembly, node):
            return True

        def propose(self, assembly, node, rng):
            return [RuleProposal(self.name, [node.node_id], {}, self.weight)]

    class EndRule:
        name = "EndGeneration"
        weight = 1

    assembly = make_default_cantilever_scenario()
    assembly.state = GenerationState.GO
    assembly.node("2").type = NodeType.FLOAT
    expected_ids = []
    selected_ids = []
    for seed in range(12):
        expected_rng = __import__("random").Random(seed)
        expected_ids.append(assembly.active_nodes()[expected_rng.randrange(0, 3)].node_id)
        kernel = VectorGSKernelV1(
            rules=[StartRule(), NodeRule(), EndRule()],
            seed=seed,
            policy_id=GDGS_NODE_RULE_UNIFORM_POLICY_ID,
        )
        proposal, context = kernel._gdgs_node_first_selection(assembly)
        selected_ids.append(context["selected_active_node"])
        assert proposal.target_node_ids == [context["selected_active_node"]]
        assert context["selected_rule_family"] == "NodeRule"

    assert selected_ids == expected_ids
    assert "2" in selected_ids


def test_gdgs_policy_excludes_empty_family_and_selects_feasible_proposal_without_mutation():
    class EmptyRule:
        name = "EmptyRule"
        weight = 1
        family = CONNECTIVITY_FAMILY

        def applicable_to(self, assembly, node):
            return True

        def propose(self, assembly, node, rng):
            return []

    class FeasibleRule:
        name = "FeasibleRule"
        weight = 1
        family = CONNECTIVITY_FAMILY

        def applicable_to(self, assembly, node):
            return node.node_id == "0"

        def propose(self, assembly, node, rng):
            if node.node_id != "0":
                return []
            return [RuleProposal(self.name, [node.node_id], {"feasible": True}, self.weight)]

    assembly = make_default_cantilever_scenario()
    assembly.state = GenerationState.GO
    before = assembly.to_data()
    kernel = VectorGSKernelV1(
        rules=[EmptyRule(), FeasibleRule()],
        seed=0,
        policy_id=GDGS_NODE_RULE_UNIFORM_POLICY_ID,
    )

    proposal, context = kernel._gdgs_node_first_selection(assembly)

    assert proposal.rule_name == "FeasibleRule"
    assert proposal.target_node_ids == ["0"]
    assert context["eligible_active_nodes"] == ["0"]
    assert context["applicable_rule_families"] == ["FeasibleRule"]
    assert context["selected_rule_family"] == "FeasibleRule"
    assert assembly.to_data() == before


def test_gdgs_policy_equal_weights_are_uniform_by_rule_family():
    class Rule:
        def __init__(self, name, weight=1):
            self.name = name
            self.weight = weight

    kernel = VectorGSKernelV1(seed=0, policy_id=GDGS_NODE_RULE_UNIFORM_POLICY_ID)
    families = [Rule("CreateNode"), Rule("SplitNode"), Rule("CloseStructure")]

    assert kernel._rule_family_probabilities(families) == pytest.approx([1.0 / 3.0] * 3)


def test_gdgs_node_first_policy_is_distinct_from_proposal_instance_uniform():
    assert GDGS_NODE_RULE_UNIFORM_POLICY_ID != "rule_uniform_random_v1"


@pytest.mark.parametrize(
    "state,expected_rules",
    [
        (GenerationState.START, {"StartGeneration"}),
        (
            GenerationState.GO,
            {
                "CreateNode",
                "ExtendNode",
                "SplitNode",
                "ConnectTwoNodes",
                "ExtendAndConnectTwoNodes",
            },
        ),
        (GenerationState.CLOSE, {"CloseStructure"}),
        (VERIFY_PHASE, {"EndGeneration"}),
        (GenerationState.END, set()),
        (INCOMPLETE_PHASE, set()),
    ],
)
def test_phase_admissibility_filters_rule_families_before_selection(state, expected_rules):
    assembly = make_default_cantilever_scenario()
    assembly.state = state
    kernel = VectorGSKernelV1(seed=0)

    assert {rule.name for rule in kernel._rules_for_phase(assembly)} == expected_rules


def test_phase_machine_completes_after_growth_and_progressive_closure():
    assembly = make_default_cantilever_scenario()
    final, trace = VectorGSKernelV1(
        seed=48,
        policy_id=GDGS_NODE_RULE_UNIFORM_POLICY_ID,
        growth_limit=4,
    ).run(assembly, max_steps=30)

    transitions = [
        (step["phase_before"], step["phase_after"], step["phase_transition_reason"])
        for step in trace
        if step["phase_before"] != step["phase_after"]
    ]
    assert transitions == [
        ("start", "grow", "initialized"),
        ("grow", "close", "growth_limit_reached"),
        ("close", "verify", "force_fronts_resolved"),
        ("verify", "end", "verification_passed"),
    ]
    assert final.state == GenerationState.END
    assert final.metadata["termination_reason"] == "completed"
    assert final.metadata["growth_step_count"] == 4
    assert final.metadata["closure_step_count"] == 3
    assert all(step["rule"] != "CloseStructure" for step in trace if step["phase_before"] == "grow")
    assert all(
        step["rule"] in {None, "CloseStructure"}
        for step in trace
        if step["phase_before"] == "close"
    )
    assert trace[-1]["assembly_after"] == final.to_data()


def test_phase_machine_reports_no_valid_closure_without_returning_to_grow():
    assembly = make_default_cantilever_scenario()
    final, trace = VectorGSKernelV1(
        seed=10,
        policy_id=GDGS_NODE_RULE_UNIFORM_POLICY_ID,
        growth_limit=4,
    ).run(assembly, max_steps=30)

    assert final.state == INCOMPLETE_PHASE
    assert final.metadata["termination_reason"] == "no_valid_closure"
    assert (trace[-1]["phase_before"], trace[-1]["phase_after"]) == ("close", "incomplete")
    close_started = next(index for index, step in enumerate(trace) if step["phase_after"] == "close")
    assert all(step["phase_after"] != "grow" for step in trace[close_started:])
    diagnostics = trace[-1]["params"]["closure_diagnostics"]
    assert diagnostics["diagnostic_reason"]
    assert "candidate_intersections" in diagnostics


def test_phase_machine_filters_crossing_closure_before_verification():
    assembly = make_default_cantilever_scenario()
    final, trace = VectorGSKernelV1(
        seed=19,
        policy_id=GDGS_NODE_RULE_UNIFORM_POLICY_ID,
        growth_limit=4,
    ).run(assembly, max_steps=30)

    assert final.state == INCOMPLETE_PHASE
    assert final.metadata["termination_reason"] == "no_valid_closure"
    assert trace[-1]["phase_before"] == "close"
    assert trace[-1]["phase_after"] == "incomplete"
    assert trace[-1]["rule"] is None
    assert all(step["phase_before"] != "verify" for step in trace)


def test_phase_machine_is_deterministic_for_same_seed_and_limits():
    first, first_trace = VectorGSKernelV1(
        seed=4,
        policy_id=GDGS_NODE_RULE_UNIFORM_POLICY_ID,
        growth_limit=4,
    ).run(make_default_cantilever_scenario(), max_steps=30)
    second, second_trace = VectorGSKernelV1(
        seed=4,
        policy_id=GDGS_NODE_RULE_UNIFORM_POLICY_ID,
        growth_limit=4,
    ).run(make_default_cantilever_scenario(), max_steps=30)

    assert first_trace == second_trace
    assert first.to_data() == second.to_data()


def test_phase_machine_verification_is_independent_of_evaluator(monkeypatch):
    import morph_engine.vector_gs_kernel_v1.metrics as metrics_module

    def evaluator_must_not_run_during_generation(*args, **kwargs):
        raise AssertionError("generation verification consumed evaluator metrics")

    monkeypatch.setattr(metrics_module, "compute_kernel_metrics", evaluator_must_not_run_during_generation)

    final, trace = VectorGSKernelV1(
        seed=48,
        policy_id=GDGS_NODE_RULE_UNIFORM_POLICY_ID,
        growth_limit=4,
    ).run(make_default_cantilever_scenario(), max_steps=30)

    assert final.state == GenerationState.END
    assert trace[-1]["phase_before"] == "verify"
    assert trace[-1]["phase_after"] == "end"
    assert trace[-1]["phase_transition_reason"] == "verification_passed"


def test_step_budget_exhaustion_is_distinct_and_terminal():
    final, trace = VectorGSKernelV1(seed=0, growth_limit=4).run(
        make_default_cantilever_scenario(),
        max_steps=1,
    )

    assert final.state == INCOMPLETE_PHASE
    assert final.metadata["termination_reason"] == "step_budget_exhausted"
    assert trace[-1]["phase_transition_reason"] == "step_budget_exhausted"


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
