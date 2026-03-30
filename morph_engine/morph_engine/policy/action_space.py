from dataclasses import dataclass, field

from morph_engine.grammar.actions import GrammarAction
from morph_engine.grammar.actions import coerce_to_grammar_action


@dataclass
class ActionBundle:
    actions: list[GrammarAction]
    mask: list[int]
    metadata: list[dict] = field(default_factory=list)
    ordering_policy: str = "grammar_proposal_order_v1"

    @property
    def action_count(self):
        return len(self.actions)

    @property
    def admissible_action_count(self):
        return sum(1 for value in self.mask if int(value) == 1)

    def admissible_actions(self):
        return [action for action, allowed in zip(self.actions, self.mask) if int(allowed) == 1]

    def action_summaries(self):
        summaries = []
        for index, action in enumerate(self.actions):
            metadata = self.metadata[index] if index < len(self.metadata) else {}
            summaries.append(
                {
                    "index": index,
                    "action_id": action.action_id,
                    "abstract_rule_id": action.abstract_rule_id,
                    "abstract_rule_name": action.abstract_rule_name,
                    "method_family": action.method_family,
                    "implementation_rule_name": action.implementation_rule_name,
                    "operator_strategy": action.operator_strategy,
                    "target_node_ids": list(action.target_node_ids),
                    "target_edge_ids": [list(edge) for edge in action.target_edge_ids],
                    "mask": int(self.mask[index]) if index < len(self.mask) else 0,
                    "metadata": dict(metadata),
                }
            )
        return summaries

    def to_summary(self):
        return {
            "ordering_policy": self.ordering_policy,
            "action_count": self.action_count,
            "admissible_action_count": self.admissible_action_count,
            "mask": [int(value) for value in self.mask],
            "actions": self.action_summaries(),
        }


def enumerate_applicable_actions(state, grammar, method_family="vector_gs"):
    if hasattr(grammar, "propose_actions"):
        actions = grammar.propose_actions(state, method_family=method_family)
        for action in actions:
            if not isinstance(action, GrammarAction):
                raise TypeError("Expected GrammarAction from grammar.propose_actions")
        return actions

    actions = []
    for proposed in grammar.propose(state):
        grammar_action = coerce_to_grammar_action(proposed, method_family=method_family)
        if not isinstance(grammar_action, GrammarAction):
            raise TypeError("Expected GrammarAction compatibility wrapper")
        actions.append(grammar_action)
    return actions


def build_action_bundle(actions, mask=None, metadata=None, ordering_policy="grammar_proposal_order_v1"):
    bundle_actions = list(actions or [])
    bundle_mask = [1] * len(bundle_actions) if mask is None else [int(value) for value in mask]
    if len(bundle_mask) != len(bundle_actions):
        raise ValueError("Action mask length must match actions length")

    bundle_metadata = list(metadata or [{} for _ in bundle_actions])
    if len(bundle_metadata) != len(bundle_actions):
        raise ValueError("Action metadata length must match actions length")

    for action in bundle_actions:
        if not isinstance(action, GrammarAction):
            raise TypeError("ActionBundle expects GrammarAction instances")

    return ActionBundle(
        actions=bundle_actions,
        mask=bundle_mask,
        metadata=bundle_metadata,
        ordering_policy=str(ordering_policy),
    )


def enumerate_action_bundle(state, grammar, method_family="vector_gs"):
    actions = enumerate_applicable_actions(state, grammar, method_family=method_family)
    return build_action_bundle(actions)
