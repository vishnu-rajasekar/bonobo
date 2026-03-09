import random

from morph_engine.evaluator.channels.global_equilibrium_v1 import GlobalEquilibriumChannel
from morph_engine.evaluator.channels.reaction_absorption_v1 import ReactionAbsorptionChannel
from morph_engine.evaluator.channels.unbalanced_force_v1 import UnbalancedForceChannel
from morph_engine.evaluator.evaluator import Evaluator
from morph_engine.experiments.logger_v1 import ExperimentLogger
from morph_engine.grammar.grammar_engine import GrammarEngine
from morph_engine.grammar.rules.extend_node import ExtendNode
from morph_engine.model.structural_graph import StructuralGraph
from morph_engine.grammar.rules.resolve_temp_force_v1 import ResolveTempForceV1
from morph_engine.grammar.rules.connect_nodes import ConnectNodes

class ExperimentRunner:
    def __init__(self, config):
        self.config = dict(config or {})
        self.logger = ExperimentLogger()
        seed = self.config.get("seed", 0)
        random.seed(seed)

    def initialize_graph(self):
        graph = StructuralGraph()
        graph.add_node("0", (0, 0, 0), fixed=[1, 1, 1])
        graph.add_node("1", (5, 0, 0), fixed=[0, 0, 0])
        graph.add_edge("0", "1", family="bar")
        graph.add_load("0", [0, -10, 0])
        graph.set_temp_force("0", [0, -10, 0])
        return graph

    def run(self):
        graph = self.initialize_graph()
        trace = []

        # grammar_engine = GrammarEngine([ExtendNode()])

        # grammar_engine = GrammarEngine([
        #     ResolveTempForceV1(step_length=2.0),
        # ])
        grammar_engine = GrammarEngine([
            ResolveTempForceV1(step_length=2.0),
            ConnectNodes(),
        ])
        evaluator = Evaluator(
            [
                ReactionAbsorptionChannel(),
                UnbalancedForceChannel(),
                GlobalEquilibriumChannel(),
            ]
        )
        result = evaluator.evaluate(graph)

        max_steps = int(self.config.get("max_steps", 20))
        for step in range(max_steps):
            candidates = grammar_engine.propose(graph)
            if not candidates:
                break

            chosen = random.choice(candidates)
            graph = grammar_engine.apply(graph, chosen)
            trace.append(
                {
                    "step": step,
                    "action": "{0}:{1}".format(chosen.rule_name, chosen.payload),
                }
            )

            result = evaluator.evaluate(graph)
            channel_result = result["channels"].get("global_equilibrium_v1", {})
            if channel_result.get("valid", False):
                break

        result["steps_executed"] = len(trace)
        self.logger.save_config(self.config)
        self.logger.save_graph(graph)
        self.logger.save_trace(trace)
        self.logger.save_metrics(result)

        return graph, result
