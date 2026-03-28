import tempfile

from morph_engine.experiments.benchmark_scenarios import get_benchmark_recovery_modes
from morph_engine.experiments.benchmark_scenarios import get_benchmark_scenario
from morph_engine.experiments.generate_structure import StructureGenerationExperiment
from morph_engine.experiments.logger_v1 import ExperimentLogger
from morph_engine.grammar.actions import GrammarAction
from morph_engine.grammar.actions import coerce_to_grammar_action
from morph_engine.grammar.grammar_engine import GrammarEngine
from morph_engine.grammar.rules.extend_node_rule import ExtendNodeRule
from morph_engine.grammar.vector_gs.rules import get_vector_gs_rule_binding


def _active_seed_graph():
    scenario = get_benchmark_scenario()
    experiment = StructureGenerationExperiment(scenario=scenario)
    return experiment.initialize_graph()


def test_coerce_extend_runtime_proposal_to_grammar_action():
    graph = _active_seed_graph()
    rule = ExtendNodeRule(lmin=1.0, lmax=1.0, seed=0)
    proposal = rule.propose(graph)[0]

    action = coerce_to_grammar_action(proposal)

    assert isinstance(action, GrammarAction)
    assert action.abstract_rule_id == "extend_node"
    assert action.abstract_rule_name == "ExtendNodeRule"
    assert action.method_family == "vector_gs"
    assert action.implementation_rule_name == "extend_node_rule"
    assert action.operator_strategy == "vector_loa_extension"
    assert action.topology_delta["nodes"] == 1
    assert action.topology_delta["edges"] == 1
    assert action.metadata["binding_provisional"] is True


def test_grammar_engine_exposes_grammar_actions():
    graph = _active_seed_graph()
    grammar = GrammarEngine([ExtendNodeRule(lmin=1.0, lmax=1.0, seed=0)])

    actions = grammar.propose_actions(graph)

    assert len(actions) == 1
    assert isinstance(actions[0], GrammarAction)
    assert actions[0].abstract_rule_id == "extend_node"
    assert actions[0].payload["node"] == "2"


def test_vector_gs_runtime_bindings_are_marked_provisional():
    extend_connect = get_vector_gs_rule_binding(implementation_rule_name="single_node_root_link_rule")
    close_structure = get_vector_gs_rule_binding(implementation_rule_name="triangle_closure_rule")
    connect = get_vector_gs_rule_binding(implementation_rule_name="resolve_two_forces_rule")

    assert extend_connect.provisional is True
    assert close_structure.provisional is True
    assert connect.provisional is True


def test_benchmark_trace_logs_action_language_metadata():
    scenario = get_benchmark_recovery_modes()[0]
    scenario["max_iterations"] = 1
    with tempfile.TemporaryDirectory() as tmpdir:
        experiment = StructureGenerationExperiment(scenario=scenario, logger=ExperimentLogger(base_path=tmpdir))
        _, result, _ = experiment.run()

    extend_evaluation = next(
        item for item in result["trace"][1]["candidate_evaluations"] if item["abstract_rule_id"] == "extend_node"
    )
    assert extend_evaluation["abstract_rule_name"] == "ExtendNodeRule"
    assert extend_evaluation["method_family"] == "vector_gs"
    assert extend_evaluation["operator_strategy"] == "vector_loa_extension"
    assert extend_evaluation["metadata"]["binding_provisional"] is True
