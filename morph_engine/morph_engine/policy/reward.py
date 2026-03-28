from dataclasses import dataclass, field


@dataclass
class RewardSpec:
    objective_weights: dict[str, float] = field(default_factory=dict)
    hard_constraints: dict[str, object] = field(default_factory=dict)
    prompt_tags: list[str] = field(default_factory=list)
    benchmark_mode: str | None = None
    phase_bias: dict[str, float] = field(default_factory=dict)


def compute_step_reward(prev_state, action, next_state, reward_spec):
    return {
        "total_reward": 0.0,
        "components": {},
        "action_id": getattr(action, "action_id", None),
        "benchmark_mode": getattr(reward_spec, "benchmark_mode", None),
    }
