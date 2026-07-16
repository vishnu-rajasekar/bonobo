import random

from .model import GenerationState
from .rules import default_rules


GDGS_NODE_RULE_UNIFORM_POLICY_ID = "gdgs_node_rule_uniform_v1"
PROPOSAL_INSTANCE_UNIFORM_POLICY_ID = "rule_uniform_random_v1"
RULE_WEIGHTED_RANDOM_POLICY_ID = "rule_weighted_random_v1"


class VectorGSKernelV1:
    def __init__(self, rules=None, seed=0, policy_id="rule_weighted_random_v1"):
        self.rules = rules or default_rules()
        self.rng = random.Random(seed)
        self.policy_id = str(policy_id)

    def _pick_node(self, assembly):
        active = assembly.active_nodes()
        if not active:
            return None
        return active[self.rng.randrange(0, len(active))]

    def _gdgs_node_first_selection(self, assembly):
        eligible_with_families = []
        for node in assembly.active_nodes():
            families = [rule for rule in self.rules[1:-1] if rule.applicable_to(assembly, node)]
            if families:
                eligible_with_families.append((node, families))
        eligible = [item[0] for item in eligible_with_families]
        context = {
            "eligible_active_nodes": [node.node_id for node in eligible],
            "selected_active_node": None,
            "applicable_rule_families": [],
            "rule_family_weights": {},
            "selected_rule_family": None,
        }
        if not eligible:
            return None, context
        node, families = eligible_with_families[self.rng.randrange(0, len(eligible_with_families))]
        context["selected_active_node"] = node.node_id
        context["applicable_rule_families"] = [rule.name for rule in families]
        context["rule_family_weights"] = {rule.name: max(1, rule.weight) for rule in families}
        if not families:
            return None, context
        probabilities = self._rule_family_probabilities(families)
        pick = self.rng.uniform(0.0, 1.0)
        running = 0.0
        selected_rule = families[-1]
        for rule, probability in zip(families, probabilities):
            running += probability
            if pick <= running:
                selected_rule = rule
                break
        context["selected_rule_family"] = selected_rule.name
        proposals = selected_rule.propose(assembly, node, self.rng)
        return (proposals[0] if proposals else None), context

    def _rule_family_probabilities(self, families):
        if not families:
            return []
        weights = [max(1, rule.weight) for rule in families]
        total = float(sum(weights))
        return [weight / total for weight in weights]

    def _all_proposals(self, assembly):
        if assembly.state == GenerationState.START:
            return self.rules[0].propose(assembly, None, self.rng)

        if self.policy_id == PROPOSAL_INSTANCE_UNIFORM_POLICY_ID:
            proposals = []
            for node in assembly.active_nodes():
                for rule in self.rules[1:]:
                    proposals.extend(rule.propose(assembly, node, self.rng))
            if proposals:
                return proposals
            return self.rules[-1].propose(assembly, None, self.rng)

        node = self._pick_node(assembly)
        if node is None:
            return self.rules[-1].propose(assembly, None, self.rng)

        proposals = []
        for rule in self.rules[1:]:
            proposals.extend(rule.propose(assembly, node, self.rng))

        if not proposals:
            for other in assembly.active_nodes():
                if other.node_id == node.node_id:
                    continue
                for rule in self.rules[1:]:
                    proposals.extend(rule.propose(assembly, other, self.rng))
        return proposals

    def _proposal_probabilities(self, proposals):
        if not proposals:
            return []
        if self.policy_id == PROPOSAL_INSTANCE_UNIFORM_POLICY_ID:
            probability = 1.0 / float(len(proposals))
            return [probability for _ in proposals]
        if self.policy_id != RULE_WEIGHTED_RANDOM_POLICY_ID:
            raise ValueError("Unsupported kernel policy_id: {0}".format(self.policy_id))
        weights = [max(1, proposal.weight) for proposal in proposals]
        total = float(sum(weights))
        return [weight / total for weight in weights]

    def _select_proposal(self, proposals):
        if not proposals:
            return None
        if self.policy_id == PROPOSAL_INSTANCE_UNIFORM_POLICY_ID:
            return proposals[self.rng.randrange(0, len(proposals))]
        if self.policy_id != RULE_WEIGHTED_RANDOM_POLICY_ID:
            raise ValueError("Unsupported kernel policy_id: {0}".format(self.policy_id))
        total = sum(max(1, proposal.weight) for proposal in proposals)
        pick = self.rng.uniform(0.0, total)
        running = 0.0
        for proposal in proposals:
            running += max(1, proposal.weight)
            if pick <= running:
                return proposal
        return proposals[-1]

    def _rule_for(self, proposal):
        for rule in self.rules:
            if rule.name == proposal.rule_name:
                return rule
        raise KeyError(proposal.rule_name)

    def run(self, assembly, max_steps=20):
        trace = []
        exhausted_budget = True
        for _ in range(max_steps):
            if assembly.state == GenerationState.START:
                proposals = self._all_proposals(assembly)
                proposal = proposals[0] if proposals else None
                selection = {
                    "eligible_active_nodes": [node.node_id for node in assembly.active_nodes()],
                    "selected_active_node": None,
                    "applicable_rule_families": [proposal.rule_name] if proposal else [],
                    "rule_family_weights": {proposal.rule_name: proposal.weight} if proposal else {},
                    "selected_rule_family": proposal.rule_name if proposal else None,
                }
            elif self.policy_id == GDGS_NODE_RULE_UNIFORM_POLICY_ID:
                proposal, selection = self._gdgs_node_first_selection(assembly)
            else:
                proposals = self._all_proposals(assembly)
                proposal = self._select_proposal(proposals)
                eligible = [node.node_id for node in assembly.active_nodes()]
                selected_node = proposal.target_node_ids[0] if proposal and proposal.target_node_ids else None
                selection = {
                    "eligible_active_nodes": eligible,
                    "selected_active_node": selected_node,
                    "applicable_rule_families": sorted({item.rule_name for item in proposals}),
                    "rule_family_weights": {item.rule_name: item.weight for item in proposals},
                    "selected_rule_family": proposal.rule_name if proposal else None,
                }
            if proposal is None:
                exhausted_budget = False
                if assembly.active_nodes():
                    active_count = len(assembly.active_nodes())
                    assembly.metadata["termination_reason"] = (
                        "no_valid_closure"
                        if active_count >= 2 and len(assembly.history) > 4
                        else "no_applicable_rules"
                    )
                else:
                    assembly.metadata.setdefault("termination_reason", "no_active_nodes")
                break
            rule = self._rule_for(proposal)
            assembly_before = assembly.to_data()
            active_front_count_before = len(assembly.active_nodes())
            before_nodes = len(assembly.nodes)
            before_members = len(assembly.members)
            assembly = rule.apply(assembly, proposal, self.rng)
            trace.append(
                {
                    "step": len(trace),
                    "state": assembly.state,
                    "rule": proposal.rule_name,
                    "targets": list(proposal.target_node_ids),
                    "params": dict(proposal.params),
                    **selection,
                    "node_count": len(assembly.nodes),
                    "member_count": len(assembly.members),
                    "added_nodes": len(assembly.nodes) - before_nodes,
                    "added_members": len(assembly.members) - before_members,
                    "residual_magnitude": assembly.residual_magnitude(),
                    "active_front_count_before": active_front_count_before,
                    "active_front_count_after": len(assembly.active_nodes()),
                    "assembly_before": assembly_before,
                    "assembly_after": assembly.to_data(),
                }
            )
            if assembly.state == GenerationState.END:
                exhausted_budget = False
                break
        if exhausted_budget and assembly.state != GenerationState.END:
            assembly.metadata["termination_reason"] = "step_budget_exhausted"
        if trace:
            trace[-1]["assembly_after"] = assembly.to_data()
        return assembly, trace
