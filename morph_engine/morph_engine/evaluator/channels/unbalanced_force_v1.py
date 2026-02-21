from math import sqrt

from morph_engine.evaluator.base import Channel


class UnbalancedForceChannel(Channel):
    name = "unbalanced_force_v1"

    def __init__(self, eps=1e-6):
        self.eps = eps

    def evaluate(self, graph):
        node_imbalance = {}
        global_imbalance = 0.0
        max_node_imbalance = 0.0

        for node_key in graph.network.nodes():
            temp_force = graph.get_temp_force(node_key)
            if len(temp_force) != 3:
                raise ValueError("temp_force must be length 3: [fx, fy, fz]")

            fx, fy, fz = temp_force
            magnitude = sqrt(fx * fx + fy * fy + fz * fz)
            node_imbalance[str(node_key)] = magnitude
            global_imbalance += magnitude
            if magnitude > max_node_imbalance:
                max_node_imbalance = magnitude

        done = global_imbalance < self.eps

        return {
            "valid": True,
            "metrics": {
                "global_imbalance": global_imbalance,
                "max_node_imbalance": max_node_imbalance,
            },
            "signals": {
                "node_imbalance": node_imbalance,
                "done": done,
            },
        }
