import random

from .model import ForceKind
from .model import GenerationState
from .rules import CLOSURE_FAMILY
from .rules import CONNECTIVITY_FAMILY
from .rules import CREATION_FAMILY
from .rules import INITIALIZATION_FAMILY
from .rules import MODIFICATION_FAMILY
from .rules import VERIFICATION_FAMILY
from .rules import default_rules
from .rules import rule_family


GDGS_NODE_RULE_UNIFORM_POLICY_ID = "gdgs_node_rule_uniform_v1"
PROPOSAL_INSTANCE_UNIFORM_POLICY_ID = "rule_uniform_random_v1"
RULE_WEIGHTED_RANDOM_POLICY_ID = "rule_weighted_random_v1"

GROW_PHASE = GenerationState.GO
VERIFY_PHASE = "verify"
INCOMPLETE_PHASE = "incomplete"

_GROW_FAMILIES = {CREATION_FAMILY, MODIFICATION_FAMILY, CONNECTIVITY_FAMILY}
_TERMINAL_PHASES = {GenerationState.END, INCOMPLETE_PHASE}


def semantic_phase(state):
    if state == GenerationState.GO:
        return "grow"
    return str(state)


class VectorGSKernelV1:
    def __init__(self, rules=None, seed=0, policy_id="rule_weighted_random_v1", growth_limit=None):
        self.rules = rules or default_rules()
        self.rng = random.Random(seed)
        self.policy_id = str(policy_id)
        self.growth_limit = self._resolve_growth_limit(growth_limit)
        if self.policy_id not in {
            GDGS_NODE_RULE_UNIFORM_POLICY_ID,
            PROPOSAL_INSTANCE_UNIFORM_POLICY_ID,
            RULE_WEIGHTED_RANDOM_POLICY_ID,
        }:
            raise ValueError("Unsupported kernel policy_id: {0}".format(self.policy_id))

    def _resolve_growth_limit(self, growth_limit):
        if growth_limit is not None:
            limit = int(growth_limit)
        else:
            close_rule = next((rule for rule in self.rules if rule.name == "CloseStructure"), None)
            limit = int(getattr(close_rule, "loopcount", 4))
        if limit < 0:
            raise ValueError("growth_limit must be non-negative")
        return limit

    def _rules_for_phase(self, assembly):
        phase = assembly.state
        if phase == GenerationState.START:
            families = {INITIALIZATION_FAMILY}
        elif phase == GROW_PHASE:
            families = _GROW_FAMILIES
        elif phase == GenerationState.CLOSE:
            families = {CLOSURE_FAMILY}
        elif phase == VERIFY_PHASE:
            families = {VERIFICATION_FAMILY}
        else:
            return []
        return [rule for rule in self.rules if rule_family(rule) in families]

    def _pick_node(self, assembly):
        active = assembly.active_nodes()
        if not active:
            return None
        return active[self.rng.randrange(0, len(active))]

    def _gdgs_node_first_selection(self, assembly):
        eligible_with_families = []
        phase_rules = self._rules_for_phase(assembly)
        for node in assembly.active_nodes():
            feasible_families = []
            for rule in phase_rules:
                proposals = rule.propose(assembly, node, self.rng)
                if proposals:
                    feasible_families.append((rule, proposals))
            if feasible_families:
                eligible_with_families.append((node, feasible_families))
        eligible = [item[0] for item in eligible_with_families]
        context = self._selection_context(eligible)
        if not eligible:
            return None, context
        node, feasible_families = eligible_with_families[
            self.rng.randrange(0, len(eligible_with_families))
        ]
        families = [item[0] for item in feasible_families]
        context["selected_active_node"] = node.node_id
        context["applicable_rule_families"] = [rule.name for rule in families]
        context["rule_family_weights"] = {rule.name: max(1, rule.weight) for rule in families}
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
        selected_proposals = next(
            proposals
            for rule, proposals in feasible_families
            if rule is selected_rule
        )
        return selected_proposals[0], context

    def _rule_family_probabilities(self, families):
        if not families:
            return []
        weights = [max(1, rule.weight) for rule in families]
        total = float(sum(weights))
        return [weight / total for weight in weights]

    def _all_proposals(self, assembly):
        phase_rules = self._rules_for_phase(assembly)
        if assembly.state in {GenerationState.START, VERIFY_PHASE}:
            proposals = []
            for rule in phase_rules:
                proposals.extend(rule.propose(assembly, None, self.rng))
            return proposals

        proposals = []
        for node in assembly.active_nodes():
            for rule in phase_rules:
                proposals.extend(rule.propose(assembly, node, self.rng))
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

    def _selection_context(self, eligible=()):
        return {
            "eligible_active_nodes": [node.node_id for node in eligible],
            "selected_active_node": None,
            "applicable_rule_families": [],
            "rule_family_weights": {},
            "selected_rule_family": None,
        }

    def _growth_selection(self, assembly):
        if self.policy_id == GDGS_NODE_RULE_UNIFORM_POLICY_ID:
            return self._gdgs_node_first_selection(assembly)
        if self.policy_id == PROPOSAL_INSTANCE_UNIFORM_POLICY_ID:
            proposals = self._all_proposals(assembly)
        else:
            proposals = self._weighted_growth_proposals(assembly)
        proposal = self._select_proposal(proposals)
        context = self._selection_context(assembly.active_nodes())
        context.update(
            {
                "selected_active_node": proposal.target_node_ids[0]
                if proposal and proposal.target_node_ids
                else None,
                "applicable_rule_families": sorted({item.rule_name for item in proposals}),
                "rule_family_weights": {item.rule_name: item.weight for item in proposals},
                "selected_rule_family": proposal.rule_name if proposal else None,
            }
        )
        return proposal, context

    def _weighted_growth_proposals(self, assembly):
        phase_rules = self._rules_for_phase(assembly)
        node = self._pick_node(assembly)
        if node is None:
            return []
        proposals = []
        for rule in phase_rules:
            proposals.extend(rule.propose(assembly, node, self.rng))
        if proposals:
            return proposals
        for other in assembly.active_nodes():
            if other.node_id == node.node_id:
                continue
            for rule in phase_rules:
                proposals.extend(rule.propose(assembly, other, self.rng))
        return proposals

    def _closure_selection(self, assembly):
        proposals = self._all_proposals(assembly)
        proposal = proposals[self.rng.randrange(0, len(proposals))] if proposals else None
        context = self._selection_context(assembly.active_nodes())
        context.update(
            {
                "selected_active_node": proposal.target_node_ids[0]
                if proposal and proposal.target_node_ids
                else None,
                "applicable_rule_families": ["CloseStructure"] if proposals else [],
                "rule_family_weights": {"CloseStructure": 1} if proposals else {},
                "selected_rule_family": proposal.rule_name if proposal else None,
            }
        )
        return proposal, context

    def _temporary_front_count(self, assembly):
        return sum(
            1
            for node in assembly.nodes
            for force in node.forces
            if force.kind == ForceKind.TEMPORARY
        )

    def _append_transition(
        self,
        trace,
        assembly,
        *,
        phase_before,
        assembly_before,
        rule=None,
        proposal=None,
        selection=None,
        phase_transition_reason=None,
        termination_reason=None,
        active_before=None,
        temporary_before=None,
        before_nodes=None,
        before_members=None,
    ):
        selection = selection or self._selection_context()
        proposal_targets = [] if proposal is None else list(proposal.target_node_ids)
        proposal_params = {} if proposal is None else dict(proposal.params)
        active_before = len(assembly.active_nodes()) if active_before is None else active_before
        temporary_before = self._temporary_front_count(assembly) if temporary_before is None else temporary_before
        before_nodes = len(assembly.nodes) if before_nodes is None else before_nodes
        before_members = len(assembly.members) if before_members is None else before_members
        trace.append(
            {
                "step": len(trace),
                "state": assembly.state,
                "phase_before": semantic_phase(phase_before),
                "phase_after": semantic_phase(assembly.state),
                "phase_transition_reason": phase_transition_reason,
                "termination_reason": termination_reason,
                "rule_family": None if rule is None else rule_family(rule),
                "rule": None if proposal is None else proposal.rule_name,
                "targets": proposal_targets,
                "params": proposal_params,
                **selection,
                "node_count": len(assembly.nodes),
                "member_count": len(assembly.members),
                "added_nodes": len(assembly.nodes) - before_nodes,
                "added_members": len(assembly.members) - before_members,
                "residual_magnitude": assembly.residual_magnitude(),
                "active_front_count_before": active_before,
                "active_front_count_after": len(assembly.active_nodes()),
                "temporary_front_count_before": temporary_before,
                "temporary_front_count_after": self._temporary_front_count(assembly),
                "assembly_before": assembly_before,
                "assembly_after": assembly.to_data(),
            }
        )

    def _automatic_transition(self, trace, assembly, state, reason, termination_reason=None):
        phase_before = assembly.state
        assembly_before = assembly.to_data()
        assembly.state = state
        if termination_reason is not None:
            assembly.metadata["termination_reason"] = termination_reason
        self._append_transition(
            trace,
            assembly,
            phase_before=phase_before,
            assembly_before=assembly_before,
            phase_transition_reason=reason,
            termination_reason=termination_reason,
        )

    def run(self, assembly, max_steps=20):
        trace = []
        operation_count = 0
        growth_step_count = 0
        closure_step_count = 0
        assembly.metadata["growth_limit"] = self.growth_limit
        assembly.metadata["step_budget"] = int(max_steps)

        while operation_count < int(max_steps) and assembly.state not in _TERMINAL_PHASES:
            if assembly.state == GROW_PHASE and growth_step_count >= self.growth_limit:
                assembly.metadata["closure_started_at_step"] = len(trace)
                self._automatic_transition(trace, assembly, GenerationState.CLOSE, "growth_limit_reached")
                continue
            if assembly.state == GenerationState.CLOSE and not assembly.active_nodes():
                self._automatic_transition(trace, assembly, VERIFY_PHASE, "force_fronts_resolved")
                continue

            if assembly.state == GenerationState.START:
                proposals = self._all_proposals(assembly)
                proposal = proposals[0] if proposals else None
                selection = self._selection_context(assembly.active_nodes())
                if proposal is not None:
                    selection["applicable_rule_families"] = [proposal.rule_name]
                    selection["rule_family_weights"] = {proposal.rule_name: proposal.weight}
                    selection["selected_rule_family"] = proposal.rule_name
            elif assembly.state == GROW_PHASE:
                proposal, selection = self._growth_selection(assembly)
            elif assembly.state == GenerationState.CLOSE:
                proposal, selection = self._closure_selection(assembly)
            elif assembly.state == VERIFY_PHASE:
                proposals = self._all_proposals(assembly)
                proposal = proposals[0] if proposals else None
                selection = self._selection_context()
                if proposal is not None:
                    selection["applicable_rule_families"] = [proposal.rule_name]
                    selection["rule_family_weights"] = {proposal.rule_name: proposal.weight}
                    selection["selected_rule_family"] = proposal.rule_name
            else:
                break

            if proposal is None:
                if assembly.state == GenerationState.CLOSE:
                    self._automatic_transition(
                        trace,
                        assembly,
                        INCOMPLETE_PHASE,
                        "no_valid_closure",
                        "no_valid_closure",
                    )
                elif assembly.state == GROW_PHASE:
                    self._automatic_transition(
                        trace,
                        assembly,
                        INCOMPLETE_PHASE,
                        "no_applicable_growth_rules",
                        "no_applicable_growth_rules",
                    )
                else:
                    self._automatic_transition(
                        trace,
                        assembly,
                        INCOMPLETE_PHASE,
                        "structurally_invalid",
                        "structurally_invalid",
                    )
                break

            rule = self._rule_for(proposal)
            phase_before = assembly.state
            assembly_before = assembly.to_data()
            active_before = len(assembly.active_nodes())
            temporary_before = self._temporary_front_count(assembly)
            before_nodes = len(assembly.nodes)
            before_members = len(assembly.members)
            assembly = rule.apply(assembly, proposal, self.rng)
            operation_count += 1
            if phase_before == GROW_PHASE:
                growth_step_count += 1
            elif phase_before == GenerationState.CLOSE:
                closure_step_count += 1
            self._append_transition(
                trace,
                assembly,
                phase_before=phase_before,
                assembly_before=assembly_before,
                rule=rule,
                proposal=proposal,
                selection=selection,
                phase_transition_reason=(
                    "initialized" if phase_before == GenerationState.START else
                    assembly.metadata.get("verification_transition_reason")
                    if phase_before == VERIFY_PHASE else None
                ),
                termination_reason=(
                    assembly.metadata.get("termination_reason")
                    if assembly.state in _TERMINAL_PHASES
                    else None
                ),
                active_before=active_before,
                temporary_before=temporary_before,
                before_nodes=before_nodes,
                before_members=before_members,
            )

        if assembly.state not in _TERMINAL_PHASES:
            self._automatic_transition(
                trace,
                assembly,
                INCOMPLETE_PHASE,
                "step_budget_exhausted",
                "step_budget_exhausted",
            )

        assembly.metadata["growth_step_count"] = growth_step_count
        assembly.metadata["closure_step_count"] = closure_step_count
        assembly.metadata["final_phase"] = semantic_phase(assembly.state)
        if trace:
            trace[-1]["assembly_after"] = assembly.to_data()
        return assembly, trace
