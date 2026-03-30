import tempfile

from morph_engine.experiments.benchmark_scenarios import get_benchmark_recovery_modes
from morph_engine.experiments.generate_structure import StructureGenerationExperiment
from morph_engine.experiments.logger_v1 import ExperimentLogger
from morph_engine.grammar.actions import GrammarAction
from morph_engine.grammar.grammar_engine import GrammarEngine
from morph_engine.grammar.rules.extend_node_rule import ExtendNodeRule
from morph_engine.policy import RewardSpec
from morph_engine.policy.action_space import build_action_bundle
from morph_engine.policy.action_space import enumerate_action_bundle
from morph_engine.policy.observation import extract_policy_observation
from morph_engine.policy.policies import HeuristicPolicy
from morph_engine.policy.policies import RandomPolicy
from morph_engine.policy.policies import WeightedRandomPolicy


def _seed_graph():
    scenario = get_benchmark_recovery_modes()[0]
    experiment = StructureGenerationExperiment(scenario=scenario)
    return experiment.initialize_graph()


def test_action_bundle_has_deterministic_mask_and_order():
    graph = _seed_graph()
    grammar = GrammarEngine([ExtendNodeRule(lmin=1.0, lmax=1.0, seed=0)])

    bundle = enumerate_action_bundle(graph, grammar)

    assert bundle.action_count == 1
    assert bundle.admissible_action_count == 1
    assert bundle.mask == [1]
    assert bundle.ordering_policy == "grammar_proposal_order_v1"
    assert isinstance(bundle.actions[0], GrammarAction)


def test_random_policy_returns_admissible_action():
    graph = _seed_graph()
    grammar = GrammarEngine([ExtendNodeRule(lmin=1.0, lmax=1.0, seed=0)])
    bundle = enumerate_action_bundle(graph, grammar)
    observation = extract_policy_observation(graph, action_bundle=bundle, phase="grow")

    decision = RandomPolicy().select_action(observation, bundle, RewardSpec())

    assert decision.selected_action is not None
    assert decision.selected_action.action_id in [action.action_id for action in bundle.admissible_actions()]


def test_weighted_random_policy_returns_admissible_action():
    graph = _seed_graph()
    grammar = GrammarEngine([ExtendNodeRule(lmin=1.0, lmax=1.0, seed=0)])
    bundle = enumerate_action_bundle(graph, grammar)
    observation = extract_policy_observation(graph, action_bundle=bundle, phase="grow")

    policy = WeightedRandomPolicy(rule_weights={"extend_node": 3.0})
    decision = policy.select_action(observation, bundle, RewardSpec())

    assert decision.selected_action is not None
    assert decision.selected_action.action_id in [action.action_id for action in bundle.admissible_actions()]
    assert decision.weights[decision.selected_action.action_id] > 0.0


def test_heuristic_policy_returns_admissible_action():
    graph = _seed_graph()
    grammar = GrammarEngine([ExtendNodeRule(lmin=1.0, lmax=1.0, seed=0)])
    bundle = enumerate_action_bundle(graph, grammar)
    enriched_bundle = build_action_bundle(
        bundle.actions,
        mask=bundle.mask,
        metadata=[
            {
                "residual_delta": 0.0,
                "support_distance_delta": 1.0,
                "support_hops_delta": 0.0,
                "support_reachable_delta": 0.0,
                "temp_force_delta": 0.0,
                "created_support_connection": False,
                "plausibility_pass": True,
                "added_edge_count": 1,
                "added_edge_length_total": 1.0,
            }
        ],
    )
    observation = extract_policy_observation(graph, action_bundle=enriched_bundle, phase="grow")

    decision = HeuristicPolicy().select_action(observation, enriched_bundle, RewardSpec())

    assert decision.selected_action is not None
    assert decision.selected_action.action_id in [action.action_id for action in enriched_bundle.admissible_actions()]


def test_experiment_runs_with_random_and_default_policy_and_logs_action_bundle():
    base_scenario = get_benchmark_recovery_modes()[0]
    base_scenario["max_iterations"] = 1

    with tempfile.TemporaryDirectory() as tmpdir:
        default_experiment = StructureGenerationExperiment(
            scenario=base_scenario,
            logger=ExperimentLogger(base_path=tmpdir),
        )
        _, default_result, _ = default_experiment.run()

    random_scenario = get_benchmark_recovery_modes()[0]
    random_scenario["max_iterations"] = 1
    random_scenario["policy_name"] = "random"
    random_scenario["selection_policy"] = "random"
    with tempfile.TemporaryDirectory() as tmpdir:
        random_experiment = StructureGenerationExperiment(
            scenario=random_scenario,
            logger=ExperimentLogger(base_path=tmpdir),
        )
        _, random_result, _ = random_experiment.run()

    assert default_result["summary"]["policy_name"] == "benchmark_ranked"
    assert random_result["summary"]["policy_name"] == "random"
    assert default_result["trace"][1]["action_bundle_summary"]["action_count"] >= 1
    assert random_result["trace"][1]["policy_decision_summary"]["policy_name"] == "random"
    assert default_result["trace"][1]["selected_action_id"] is not None or default_result["summary"]["termination_reason"] == "no_admissible_candidate"
