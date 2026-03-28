from dataclasses import dataclass


@dataclass(frozen=True)
class AbstractGrammarRuleSpec:
    rule_id: str
    canonical_name: str
    target_arity: str
    semantic_description: str
    expected_topology_change: str
    phase_sensitive: bool
    requires_method_realization: bool


FROZEN_ABSTRACT_RULES = [
    AbstractGrammarRuleSpec(
        rule_id="start_generation",
        canonical_name="StartGenerationRule",
        target_arity="none",
        semantic_description="Enter the generative episode and initialize phase-sensitive rule flow.",
        expected_topology_change="no immediate topology change",
        phase_sensitive=True,
        requires_method_realization=False,
    ),
    AbstractGrammarRuleSpec(
        rule_id="create_node",
        canonical_name="CreateNodeRule",
        target_arity="single_site_or_front",
        semantic_description="Create one new node without immediately committing a member pair closure pattern.",
        expected_topology_change="creates 1 node",
        phase_sensitive=True,
        requires_method_realization=True,
    ),
    AbstractGrammarRuleSpec(
        rule_id="extend_node",
        canonical_name="ExtendNodeRule",
        target_arity="single_active_front",
        semantic_description="Continue a structural front by creating one new node and one new member.",
        expected_topology_change="creates 1 node + 1 member",
        phase_sensitive=True,
        requires_method_realization=True,
    ),
    AbstractGrammarRuleSpec(
        rule_id="split_node",
        canonical_name="SplitNodeRule",
        target_arity="single_active_front",
        semantic_description="Split one active front into two structural branches from the same origin.",
        expected_topology_change="creates 1 node + 2 members",
        phase_sensitive=True,
        requires_method_realization=True,
    ),
    AbstractGrammarRuleSpec(
        rule_id="connect_two_nodes",
        canonical_name="ConnectTwoNodesRule",
        target_arity="two_existing_nodes",
        semantic_description="Create one structural member between two existing nodes.",
        expected_topology_change="creates 1 member",
        phase_sensitive=True,
        requires_method_realization=True,
    ),
    AbstractGrammarRuleSpec(
        rule_id="extend_and_connect_two_nodes",
        canonical_name="ExtendAndConnectTwoNodesRule",
        target_arity="single_active_front_plus_target",
        semantic_description="Create one new node and connect it into the structure with two members.",
        expected_topology_change="creates 1 node + 2 members",
        phase_sensitive=True,
        requires_method_realization=True,
    ),
    AbstractGrammarRuleSpec(
        rule_id="close_structure",
        canonical_name="CloseStructureRule",
        target_arity="closure_configuration",
        semantic_description="Close a structural gap with a method-specific closure motif.",
        expected_topology_change="creates 3 members",
        phase_sensitive=True,
        requires_method_realization=True,
    ),
    AbstractGrammarRuleSpec(
        rule_id="end_generation",
        canonical_name="EndGenerationRule",
        target_arity="none",
        semantic_description="Terminate the generative episode when no further valid actions should be taken.",
        expected_topology_change="no immediate topology change",
        phase_sensitive=True,
        requires_method_realization=False,
    ),
]


ABSTRACT_RULE_REGISTRY = {spec.rule_id: spec for spec in FROZEN_ABSTRACT_RULES}
