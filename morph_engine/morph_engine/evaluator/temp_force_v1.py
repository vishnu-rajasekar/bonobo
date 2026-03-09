from math import sqrt

from morph_engine.evaluator.base import Channel
from morph_engine.model.force import Force
from morph_engine.model.force import ForceDirection
from morph_engine.model.force import ForceType


class TempForceChannel(Channel):
    name = "temp_force_v1"

    def __init__(self, tolerance=1e-6):
        self.tolerance = tolerance

    def evaluate(self, graph):
        node_residuals = {}
        generated = 0

        for node_key in graph.network.nodes():
            existing = graph.get_node_forces(node_key)
            non_temp_forces = [f for f in existing if getattr(f, "type", None) != ForceType.TEMP]

            # Reset node force list to non-temp forces before recomputing closure.
            graph.network.node_attribute(node_key, "forces", list(non_temp_forces))

            residual = [0.0, 0.0, 0.0]
            for force in non_temp_forces:
                vec = force.vector
                residual[0] += float(vec[0])
                residual[1] += float(vec[1])
                residual[2] += float(vec[2])

            magnitude = sqrt(
                residual[0] * residual[0]
                + residual[1] * residual[1]
                + residual[2] * residual[2]
            )
            node_residuals[str(node_key)] = magnitude

            if magnitude > self.tolerance:
                temp = Force(
                    node_id=node_key,
                    vector=(-residual[0], -residual[1], -residual[2]),
                    type=ForceType.TEMP,
                    direction=ForceDirection.COMPRESSION,
                )
                graph.add_force_to_node(node_key, temp)
                graph.set_temp_force(node_key, temp.vector)
                generated += 1
            else:
                graph.set_temp_force(node_key, [0.0, 0.0, 0.0])

        return {
            "valid": True,
            "metrics": {
                "temp_forces_generated": generated,
            },
            "signals": {
                "node_residuals": node_residuals,
            },
        }
