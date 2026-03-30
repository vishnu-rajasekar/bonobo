from dataclasses import dataclass


@dataclass(frozen=True)
class VectorGSRuleBinding:
    abstract_rule_id: str
    abstract_rule_name: str
    implementation_rule_name: str | None
    current_module: str | None
    method_family: str
    operator_strategy: str | None
    topology_delta_summary: dict
    status: str
    provisional: bool
    notes: str


VECTOR_GS_RULE_BINDINGS = [
    VectorGSRuleBinding(
        abstract_rule_id="start_generation",
        abstract_rule_name="StartGenerationRule",
        implementation_rule_name=None,
        current_module=None,
        method_family="vector_gs",
        operator_strategy=None,
        topology_delta_summary={"nodes": 0, "edges": 0, "summary": "no immediate topology change"},
        status="interface_only",
        provisional=True,
        notes="Episode boundary intent. No separate vector GS realization is required at runtime.",
    ),
    VectorGSRuleBinding(
        abstract_rule_id="create_node",
        abstract_rule_name="CreateNodeRule",
        implementation_rule_name="create_node_rule",
        current_module="morph_engine.grammar.rules.create_node_rule",
        method_family="vector_gs",
        operator_strategy="floating_seed_from_active_loa",
        topology_delta_summary={"nodes": 1, "edges": 0, "summary": "creates 1 node"},
        status="prototype_active",
        provisional=True,
        notes="Provisional vector GS floating-seed realization adapted from Juney Rule 1. Interface remains broader than the current runtime prototype.",
    ),
    VectorGSRuleBinding(
        abstract_rule_id="extend_node",
        abstract_rule_name="ExtendNodeRule",
        implementation_rule_name="extend_node_rule",
        current_module="morph_engine.grammar.rules.extend_node_rule",
        method_family="vector_gs",
        operator_strategy="vector_loa_extension",
        topology_delta_summary={"nodes": 1, "edges": 1, "summary": "creates 1 node + 1 member"},
        status="active",
        provisional=True,
        notes="Current vector GS extend realization. Runtime mapping is provisional rather than final grammar truth.",
    ),
    VectorGSRuleBinding(
        abstract_rule_id="split_node",
        abstract_rule_name="SplitNodeRule",
        implementation_rule_name="split_node_rule",
        current_module="morph_engine.grammar.rules.split_node_rule",
        method_family="vector_gs",
        operator_strategy="vector_temp_force_split",
        topology_delta_summary={"nodes": 2, "edges": 2, "summary": "current runtime creates 2 nodes + 2 members"},
        status="active",
        provisional=True,
        notes="Current vector GS split realization. Runtime topology is provisional relative to the frozen abstract intent.",
    ),
    VectorGSRuleBinding(
        abstract_rule_id="connect_two_nodes",
        abstract_rule_name="ConnectTwoNodesRule",
        implementation_rule_name="resolve_two_forces_rule",
        current_module="morph_engine.grammar.rules.resolve_two_forces_rule",
        method_family="vector_gs",
        operator_strategy="direct_two_force_connection",
        topology_delta_summary={"nodes": 0, "edges": 1, "summary": "creates 1 member"},
        status="benchmark_optional",
        provisional=True,
        notes="Current vector GS connect realization. This is a provisional runtime strategy shim.",
    ),
    VectorGSRuleBinding(
        abstract_rule_id="extend_and_connect_two_nodes",
        abstract_rule_name="ExtendAndConnectTwoNodesRule",
        implementation_rule_name="single_node_root_link_rule",
        current_module="morph_engine.grammar.rules.single_node_root_link_rule",
        method_family="vector_gs",
        operator_strategy="root_link_projection_or_direct_support_link",
        topology_delta_summary={
            "nodes": None,
            "edges": 1,
            "summary": "benchmark-specific runtime may add 0-1 nodes and 1 member; not final abstract behavior",
        },
        status="benchmark_optional",
        provisional=True,
        notes="Benchmark-specific recovery realization. Explicitly provisional and not long-term grammar truth.",
    ),
    VectorGSRuleBinding(
        abstract_rule_id="close_structure",
        abstract_rule_name="CloseStructureRule",
        implementation_rule_name="triangle_closure_rule",
        current_module="morph_engine.grammar.rules.triangle_closure_rule",
        method_family="vector_gs",
        operator_strategy="triangle_closure_strategy",
        topology_delta_summary={"nodes": 0, "edges": 1, "summary": "current runtime adds 1 member; abstract close intent remains broader"},
        status="benchmark_active",
        provisional=True,
        notes="Current vector GS closure realization. Provisional mapping from benchmark-era runtime behavior.",
    ),
    VectorGSRuleBinding(
        abstract_rule_id="end_generation",
        abstract_rule_name="EndGenerationRule",
        implementation_rule_name=None,
        current_module=None,
        method_family="vector_gs",
        operator_strategy=None,
        topology_delta_summary={"nodes": 0, "edges": 0, "summary": "no immediate topology change"},
        status="interface_only",
        provisional=True,
        notes="Episode termination intent. Current benchmark harness owns stop conditions.",
    ),
]


IMPLEMENTATION_TO_ABSTRACT_RULE = {
    binding.implementation_rule_name: binding.abstract_rule_id
    for binding in VECTOR_GS_RULE_BINDINGS
    if binding.implementation_rule_name
}

IMPLEMENTATION_RULE_BINDINGS = {
    binding.implementation_rule_name: binding for binding in VECTOR_GS_RULE_BINDINGS if binding.implementation_rule_name
}

ABSTRACT_RULE_BINDINGS = {binding.abstract_rule_id: binding for binding in VECTOR_GS_RULE_BINDINGS}


def resolve_abstract_rule_id(implementation_rule_name):
    return IMPLEMENTATION_TO_ABSTRACT_RULE.get(str(implementation_rule_name))


def get_vector_gs_rule_binding(*, implementation_rule_name=None, abstract_rule_id=None):
    if implementation_rule_name is not None:
        return IMPLEMENTATION_RULE_BINDINGS.get(str(implementation_rule_name))
    if abstract_rule_id is not None:
        return ABSTRACT_RULE_BINDINGS.get(str(abstract_rule_id))
    return None
