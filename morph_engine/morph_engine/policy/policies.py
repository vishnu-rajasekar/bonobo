from dataclasses import dataclass, field
import random


@dataclass
class PolicyDecision:
    policy_name: str
    selected_action: object | None
    selected_index: int | None
    admissible_action_ids: list[str] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=dict)
    scores: dict[str, float] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_summary(self):
        return {
            "policy_name": self.policy_name,
            "selected_action_id": None if self.selected_action is None else self.selected_action.action_id,
            "selected_index": self.selected_index,
            "admissible_action_ids": list(self.admissible_action_ids),
            "weights": dict(self.weights),
            "scores": dict(self.scores),
            "metadata": dict(self.metadata),
        }


class BasePolicy:
    name = "base_policy"

    def select_action(self, observation, action_bundle, reward_spec, rng=None):
        raise NotImplementedError


def _rng_or_default(rng=None):
    return rng if rng is not None else random.Random(0)


def _admissible_pairs(action_bundle):
    pairs = []
    for index, (action, allowed) in enumerate(zip(action_bundle.actions, action_bundle.mask)):
        if int(allowed) == 1:
            pairs.append((index, action))
    return pairs


class RandomPolicy(BasePolicy):
    name = "random"

    def select_action(self, observation, action_bundle, reward_spec, rng=None):
        admissible = _admissible_pairs(action_bundle)
        if not admissible:
            return PolicyDecision(policy_name=self.name, selected_action=None, selected_index=None)
        local_rng = _rng_or_default(rng)
        selected_index, selected_action = local_rng.choice(admissible)
        return PolicyDecision(
            policy_name=self.name,
            selected_action=selected_action,
            selected_index=selected_index,
            admissible_action_ids=[action.action_id for _, action in admissible],
        )


class WeightedRandomPolicy(BasePolicy):
    name = "weighted_random"

    def __init__(self, rule_weights=None, operator_weights=None, base_weight=1.0):
        self.rule_weights = dict(rule_weights or {})
        self.operator_weights = dict(operator_weights or {})
        self.base_weight = float(base_weight)

    def _weight(self, action):
        weight = self.base_weight
        if action.abstract_rule_id is not None:
            weight *= float(self.rule_weights.get(action.abstract_rule_id, 1.0))
        if action.operator_strategy is not None:
            weight *= float(self.operator_weights.get(action.operator_strategy, 1.0))
        return max(weight, 1e-9)

    def select_action(self, observation, action_bundle, reward_spec, rng=None):
        admissible = _admissible_pairs(action_bundle)
        if not admissible:
            return PolicyDecision(policy_name=self.name, selected_action=None, selected_index=None)

        local_rng = _rng_or_default(rng)
        weights = {}
        population = []
        population_weights = []
        for index, action in admissible:
            weight = self._weight(action)
            weights[action.action_id] = weight
            population.append((index, action))
            population_weights.append(weight)

        selected_index, selected_action = local_rng.choices(population, weights=population_weights, k=1)[0]
        return PolicyDecision(
            policy_name=self.name,
            selected_action=selected_action,
            selected_index=selected_index,
            admissible_action_ids=[action.action_id for _, action in admissible],
            weights=weights,
        )


class HeuristicPolicy(BasePolicy):
    name = "heuristic"

    def __init__(self, objective_weights=None, selection_mode="best", top_band_size=2, name=None):
        self.objective_weights = {
            "residual_reduction": 5.0,
            "support_engagement": 3.0,
            "closure_progress": 2.0,
            "plausibility_pass": 10.0,
            "member_count_penalty": -0.2,
            "total_length_penalty": 0.0,
        }
        self.objective_weights.update(dict(objective_weights or {}))
        self.selection_mode = str(selection_mode)
        self.top_band_size = int(top_band_size)
        if name is not None:
            self.name = str(name)

    def _score(self, action, metadata, reward_spec):
        weights = dict(self.objective_weights)
        if reward_spec is not None:
            weights.update(getattr(reward_spec, "objective_weights", {}) or {})

        support_gain = (
            float(metadata.get("support_distance_delta", 0.0))
            + float(metadata.get("support_hops_delta", 0.0))
            + float(metadata.get("support_reachable_delta", 0.0))
            + (1.0 if metadata.get("created_support_connection") else 0.0)
        )
        closure_progress = float(metadata.get("temp_force_delta", 0.0)) + float(metadata.get("support_reachable_delta", 0.0))
        plausibility_pass = 1.0 if metadata.get("plausibility_pass", True) else 0.0
        member_penalty = float(metadata.get("added_edge_count", 0.0))
        length_penalty = float(metadata.get("added_edge_length_total", 0.0))

        return (
            weights.get("residual_reduction", 0.0) * float(metadata.get("residual_delta", 0.0))
            + weights.get("support_engagement", 0.0) * support_gain
            + weights.get("closure_progress", 0.0) * closure_progress
            + weights.get("plausibility_pass", 0.0) * plausibility_pass
            + weights.get("member_count_penalty", 0.0) * member_penalty
            + weights.get("total_length_penalty", 0.0) * length_penalty
        )

    def select_action(self, observation, action_bundle, reward_spec, rng=None):
        admissible = _admissible_pairs(action_bundle)
        if not admissible:
            return PolicyDecision(policy_name=self.name, selected_action=None, selected_index=None)

        if self.selection_mode == "first":
            selected_index, selected_action = admissible[0]
            return PolicyDecision(
                policy_name=self.name,
                selected_action=selected_action,
                selected_index=selected_index,
                admissible_action_ids=[action.action_id for _, action in admissible],
                metadata={"selection_mode": self.selection_mode},
            )

        scored = []
        score_map = {}
        for index, action in admissible:
            metadata = action_bundle.metadata[index] if index < len(action_bundle.metadata) else {}
            score = self._score(action, metadata, reward_spec)
            score_map[action.action_id] = score
            scored.append((score, index, action))

        scored.sort(key=lambda item: item[0], reverse=True)
        local_rng = _rng_or_default(rng)
        if self.selection_mode == "stochastic_top_band":
            top_band = scored[: max(1, self.top_band_size)]
            _, selected_index, selected_action = local_rng.choice(top_band)
        else:
            _, selected_index, selected_action = scored[0]

        return PolicyDecision(
            policy_name=self.name,
            selected_action=selected_action,
            selected_index=selected_index,
            admissible_action_ids=[action.action_id for _, action in admissible],
            scores=score_map,
            metadata={"selection_mode": self.selection_mode, "top_band_size": self.top_band_size},
        )


def resolve_policy(policy_name=None, selection_policy=None, config=None):
    config = dict(config or {})
    resolved_name = policy_name or selection_policy or "benchmark_ranked"

    if resolved_name == "random":
        return RandomPolicy()
    if resolved_name == "weighted_random":
        return WeightedRandomPolicy(
            rule_weights=config.get("rule_weights"),
            operator_weights=config.get("operator_weights"),
            base_weight=float(config.get("base_weight", 1.0)),
        )
    if resolved_name in {"heuristic", "benchmark_ranked"}:
        return HeuristicPolicy(
            objective_weights=config.get("objective_weights"),
            selection_mode="best",
            top_band_size=int(config.get("top_band_size", 2)),
            name=str(resolved_name),
        )
    if resolved_name == "first_candidate":
        return HeuristicPolicy(selection_mode="first", top_band_size=1, name="first_candidate")
    if resolved_name == "stochastic_top_band":
        return HeuristicPolicy(
            objective_weights=config.get("objective_weights"),
            selection_mode="stochastic_top_band",
            top_band_size=int(config.get("top_band_size", 2)),
            name="stochastic_top_band",
        )
    raise ValueError("Unsupported policy: {0}".format(resolved_name))
