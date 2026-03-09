from copy import deepcopy
from math import sqrt
import random

from morph_engine.grammar.base import Candidate


def _next_node_key(network):
    key = str(network.number_of_nodes())
    while key in [str(k) for k in network.nodes()]:
        key = str(int(key) + 1)
    return key


class ExtendNodeRule:
    name = "extend_node_rule"

    def __init__(self, lmin=1.0, lmax=2.0, seed=0):
        self.lmin = float(lmin)
        self.lmax = float(lmax)
        self._rng = random.Random(seed)

    def propose(self, graph):
        candidates = []
        for node_key in graph.network.nodes():
            fx, fy, fz = graph.get_temp_force(node_key)
            magnitude = sqrt(fx * fx + fy * fy + fz * fz)
            if magnitude <= 1e-8:
                continue
            length = self._rng.uniform(self.lmin, self.lmax)
            payload = {"node": node_key, "length": float(length)}
            candidates.append(Candidate(self.name, payload))
        return candidates

    def apply(self, graph, payload):
        node_key = payload["node"]
        new_graph = deepcopy(graph)

        fx, fy, fz = new_graph.get_temp_force(node_key)
        magnitude = sqrt(fx * fx + fy * fy + fz * fz)
        if magnitude <= 1e-12:
            return new_graph

        direction = [fx / magnitude, fy / magnitude, fz / magnitude]
        x, y, z = new_graph.network.node_attribute(node_key, "xyz")
        length = float(payload.get("length", (self.lmin + self.lmax) * 0.5))
        new_xyz = [
            x + length * direction[0],
            y + length * direction[1],
            z + length * direction[2],
        ]

        new_key = _next_node_key(new_graph.network)
        original_force = [fx, fy, fz]

        new_graph.add_node(new_key, new_xyz, fixed=[0, 0, 0])
        new_graph.add_edge(node_key, new_key, family="bar")
        new_graph.set_temp_force(node_key, [0.0, 0.0, 0.0])
        new_graph.set_temp_force(new_key, original_force)

        return new_graph
