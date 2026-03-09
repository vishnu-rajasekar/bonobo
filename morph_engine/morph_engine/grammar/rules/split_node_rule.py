from copy import deepcopy
from math import cos
from math import sin
from math import sqrt
import random

from morph_engine.grammar.base import Candidate


def _next_node_key(network):
    key = str(network.number_of_nodes())
    while key in [str(k) for k in network.nodes()]:
        key = str(int(key) + 1)
    return key


def _normalize(vec3):
    x, y, z = float(vec3[0]), float(vec3[1]), float(vec3[2])
    mag = sqrt(x * x + y * y + z * z)
    if mag <= 1e-12:
        return None
    return [x / mag, y / mag, z / mag]


def _rotate_z(vec3, theta):
    x, y, z = vec3
    c = cos(theta)
    s = sin(theta)
    return [x * c - y * s, x * s + y * c, z]


class SplitNodeRule:
    name = "split_node_rule"

    def __init__(self, theta_min=0.35, theta_max=0.55, length=1.0, seed=0):
        self.theta_min = float(theta_min)
        self.theta_max = float(theta_max)
        self.length = float(length)
        self._rng = random.Random(seed)

    def propose(self, graph):
        candidates = []
        for node_key in graph.network.nodes():
            direction = _normalize(graph.get_temp_force(node_key))
            if direction is None:
                continue
            theta = self._rng.uniform(self.theta_min, self.theta_max)
            candidates.append(Candidate(self.name, {"node": node_key, "theta": theta}))
        return candidates

    def apply(self, graph, payload):
        new_graph = deepcopy(graph)
        node_key = payload["node"]
        theta = float(payload["theta"])

        base_force = new_graph.get_temp_force(node_key)
        direction = _normalize(base_force)
        if direction is None:
            return new_graph

        dir1 = _rotate_z(direction, theta)
        dir2 = _rotate_z(direction, -theta)

        x, y, z = new_graph.network.node_attribute(node_key, "xyz")
        xyz_a = [
            x + self.length * dir1[0],
            y + self.length * dir1[1],
            z + self.length * dir1[2],
        ]
        xyz_b = [
            x + self.length * dir2[0],
            y + self.length * dir2[1],
            z + self.length * dir2[2],
        ]

        node_a = _next_node_key(new_graph.network)
        new_graph.add_node(node_a, xyz_a, fixed=[0, 0, 0])
        node_b = _next_node_key(new_graph.network)
        new_graph.add_node(node_b, xyz_b, fixed=[0, 0, 0])

        new_graph.add_edge(node_key, node_a, family="bar")
        new_graph.add_edge(node_key, node_b, family="bar")

        new_graph.set_temp_force(node_key, [0.0, 0.0, 0.0])
        new_graph.set_temp_force(node_a, base_force)
        new_graph.set_temp_force(node_b, base_force)
        return new_graph
