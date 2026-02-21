from math import sqrt

from morph_engine.evaluator.base import Channel


class GlobalEquilibriumChannel(Channel):
    name = "global_equilibrium_v1"

    def __init__(self, tolerance=1e-6):
        self.tolerance = tolerance

    def evaluate(self, graph, context=None):
        total_load = [0.0, 0.0, 0.0]
        for load in graph.loadcases:
            vector = load.get("vector", [0.0, 0.0, 0.0])
            total_load[0] += float(vector[0])
            total_load[1] += float(vector[1])
            total_load[2] += float(vector[2])

        if context and "reaction_absorption_v1" in context:
            total_reaction = context["reaction_absorption_v1"]["metrics"]["total_reaction"]
        else:
            total_reaction = [0.0, 0.0, 0.0]

        residual = [
            total_load[0] + float(total_reaction[0]),
            total_load[1] + float(total_reaction[1]),
            total_load[2] + float(total_reaction[2]),
        ]
        residual_magnitude = sqrt(
            residual[0] * residual[0] + residual[1] * residual[1] + residual[2] * residual[2]
        )

        return {
            "valid": residual_magnitude < self.tolerance,
            "metrics": {
                "residual_vector": residual,
                "residual_magnitude": residual_magnitude,
            },
            "signals": {},
        }
