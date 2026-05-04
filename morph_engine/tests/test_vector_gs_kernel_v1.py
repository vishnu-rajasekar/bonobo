from morph_engine.vector_gs_kernel_v1 import VectorGSKernelV1
from morph_engine.vector_gs_kernel_v1 import make_default_cantilever_scenario
from morph_engine.vector_gs_kernel_v1.model import Force
from morph_engine.vector_gs_kernel_v1.model import ForceDirection
from morph_engine.vector_gs_kernel_v1.model import ForceKind
from morph_engine.vector_gs_kernel_v1.model import GenerationState
from morph_engine.vector_gs_kernel_v1.model import Node
from morph_engine.vector_gs_kernel_v1.model import NodeType
from morph_engine.vector_gs_kernel_v1.operators import equilibrate_node
from morph_engine.vector_gs_kernel_v1.rules import RuleProposal
from morph_engine.vector_gs_kernel_v1.rules import ExtendNodeRule


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


def test_kernel_smoke_run_generates_nontrivial_structure():
    assembly = make_default_cantilever_scenario()
    kernel = VectorGSKernelV1(seed=0)
    final_assembly, trace = kernel.run(assembly, max_steps=8)

    assert trace
    assert len(final_assembly.members) >= 1
    assert any(step["rule"] != "StartGeneration" for step in trace)


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
