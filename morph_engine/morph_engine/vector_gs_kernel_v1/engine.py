import random

from .model import GenerationState
from .rules import default_rules


class VectorGSKernelV1:
    def __init__(self, rules=None, seed=0, policy_id="rule_weighted_random_v1"):
        self.rules = rules or default_rules()
        self.rng = random.Random(seed)
        self.policy_id = str(policy_id)

    def _pick_node(self, assembly):
        active = assembly.active_nodes()
        if not active:
            return None
        preferred = [node for node in active if node.type in {"support", "load"}]
        pool = preferred or active
        return pool[self.rng.randrange(0, len(pool))]

    def _all_proposals(self, assembly):
        if assembly.state == GenerationState.START:
            return self.rules[0].propose(assembly, None, self.rng)

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

    def _select_proposal(self, proposals):
        if not proposals:
            return None
        if self.policy_id == "rule_uniform_random_v1":
            return proposals[self.rng.randrange(0, len(proposals))]
        if self.policy_id != "rule_weighted_random_v1":
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
        for _ in range(max_steps):
            proposals = self._all_proposals(assembly)
            proposal = self._select_proposal(proposals)
            if proposal is None:
                assembly.state = GenerationState.END
                break
            rule = self._rule_for(proposal)
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
                    "node_count": len(assembly.nodes),
                    "member_count": len(assembly.members),
                    "added_nodes": len(assembly.nodes) - before_nodes,
                    "added_members": len(assembly.members) - before_members,
                    "residual_magnitude": assembly.residual_magnitude(),
                }
            )
            if assembly.state == GenerationState.END:
                break
        return assembly, trace
