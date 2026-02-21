from copy import deepcopy
from math import sqrt

from morph_engine.grammar.base import Candidate


def _next_node_key(network):
    key = str(network.number_of_nodes())
    while key in [str(k) for k in network.nodes()]:
        key = str(int(key) + 1)
    return key


class ResolveTempForceV1:
    name = "resolve_temp_force_v1"

    def __init__(self, step_length=2.0):
        self.step_length = step_length

    def propose(self, graph):
        candidates = []
        for node_key in graph.network.nodes():
            fx, fy, fz = graph.get_temp_force(node_key)
            magnitude = sqrt(fx * fx + fy * fy + fz * fz)
            if magnitude > 1e-8:
                candidates.append(Candidate(self.name, {"node": node_key}))
        return candidates

    def apply(self, graph, payload):
        node_key = payload["node"]
        new_graph = deepcopy(graph)

        fx, fy, fz = new_graph.get_temp_force(node_key)
        magnitude = sqrt(fx * fx + fy * fy + fz * fz)
        if magnitude == 0:
            return new_graph

        direction = [fx / magnitude, fy / magnitude, fz / magnitude]
        x, y, z = new_graph.network.node_attribute(node_key, "xyz")
        new_xyz = [
            x + self.step_length * direction[0],
            y + self.step_length * direction[1],
            z + self.step_length * direction[2],
        ]

        new_key = _next_node_key(new_graph.network)
        original_force = [fx, fy, fz]

        new_graph.add_node(new_key, new_xyz, fixed=[0, 0, 0])
        new_graph.add_edge(node_key, new_key, family="bar")
        new_graph.set_temp_force(node_key, [0, 0, 0])
        new_graph.set_temp_force(new_key, original_force)

        return new_graph
