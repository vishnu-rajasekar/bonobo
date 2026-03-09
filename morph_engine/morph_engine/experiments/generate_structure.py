import json
import os
import random

from morph_engine.evaluator.channels.global_equilibrium_v1 import GlobalEquilibriumChannel
from morph_engine.evaluator.channels.reaction_absorption_v1 import ReactionAbsorptionChannel
from morph_engine.evaluator.channels.unbalanced_force_v1 import UnbalancedForceChannel
from morph_engine.evaluator.evaluator import Evaluator
from morph_engine.experiments.logger_v1 import ExperimentLogger
from morph_engine.grammar.grammar_engine import GrammarEngine
from morph_engine.grammar.rules.extend_node_rule import ExtendNodeRule
from morph_engine.grammar.rules.split_node_rule import SplitNodeRule
from morph_engine.grammar.rules.triangle_closure_rule import TriangleClosureRule
from morph_engine.model.structural_graph import StructuralGraph


class StructureGenerationExperiment:
    def __init__(self, iterations=20, seed=0):
        self.iterations = int(iterations)
        self.seed = int(seed)
        self._rng = random.Random(self.seed)
        self.logger = ExperimentLogger()

    def initialize_graph(self):
        graph = StructuralGraph()
        graph.add_node("0", (-5.0, 0.0, 0.0), fixed=[1, 1, 1])
        graph.add_node("1", (5.0, 0.0, 0.0), fixed=[1, 1, 1])
        graph.add_node("2", (0.0, 4.0, 0.0), fixed=[0, 0, 0])
        graph.add_edge("0", "2", family="bar")
        graph.add_edge("1", "2", family="bar")
        graph.add_load("2", [0.0, -10.0, 0.0])
        graph.set_temp_force("2", [0.0, -10.0, 0.0])
        return graph

    def _snapshot_dir(self):
        run_dir = self.logger.create_run_dir()
        path = os.path.join(run_dir, "snapshots")
        os.makedirs(path, exist_ok=True)
        return path

    def _save_snapshot(self, graph, step):
        snapshot_dir = self._snapshot_dir()
        filename = "step_{0:03d}.json".format(int(step))
        with open(os.path.join(snapshot_dir, filename), "w", encoding="utf-8") as handle:
            json.dump(graph.to_json(), handle, indent=2)

    def run(self):
        graph = self.initialize_graph()
        grammar = GrammarEngine(
            [
                SplitNodeRule(theta_min=0.35, theta_max=0.65, length=2.0, seed=self.seed),
                ExtendNodeRule(lmin=1.0, lmax=2.0, seed=self.seed),
                TriangleClosureRule(radius=6.0),
            ]
        )
        evaluator = Evaluator(
            [
                ReactionAbsorptionChannel(),
                UnbalancedForceChannel(),
                GlobalEquilibriumChannel(),
            ]
        )

        trace = []
        result = evaluator.evaluate(graph)
        self._save_snapshot(graph, 0)

        for step in range(1, self.iterations + 1):
            state_before = getattr(grammar, "state", None)
            candidates = grammar.propose(graph)
            if not candidates:
                trace.append(
                    {
                        "step": step,
                        "state_before": str(state_before),
                        "state_after": str(getattr(grammar, "state", None)),
                        "action": None,
                    }
                )
                break

            chosen = candidates[0]
            graph = grammar.apply(graph, chosen)
            result = evaluator.evaluate(graph)

            trace.append(
                {
                    "step": step,
                    "state_before": str(state_before),
                    "state_after": str(getattr(grammar, "state", None)),
                    "action": "{0}:{1}".format(chosen.rule_name, chosen.payload),
                }
            )
            self._save_snapshot(graph, step)

            if result.get("channels", {}).get("global_equilibrium_v1", {}).get("valid", False):
                break

        result["steps_executed"] = len(trace)
        config = {"iterations": self.iterations, "seed": self.seed}
        self.logger.save_config(config)
        self.logger.save_graph(graph)
        self.logger.save_trace(trace)
        self.logger.save_metrics(result)
        return graph, result, self.logger.run_dir
