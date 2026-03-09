from copy import deepcopy
from math import sqrt

from morph_engine.grammar.base import Candidate


def _has_edge(network, u, v):
    try:
        return network.has_edge((u, v))
    except TypeError:
        return network.has_edge(u, v)


def _distance(network, u, v):
    ux, uy, uz = network.node_attribute(u, "xyz")
    vx, vy, vz = network.node_attribute(v, "xyz")
    dx = float(vx) - float(ux)
    dy = float(vy) - float(uy)
    dz = float(vz) - float(uz)
    return sqrt(dx * dx + dy * dy + dz * dz)


class TriangleClosureRule:
    name = "triangle_closure_rule"

    def __init__(self, radius=10.0):
        self.radius = float(radius)

    def propose(self, graph):
        nodes = list(graph.network.nodes())
        candidates = []
        for i, a in enumerate(nodes):
            for j in range(i + 1, len(nodes)):
                b = nodes[j]
                if not _has_edge(graph.network, a, b):
                    continue
                if _distance(graph.network, a, b) > self.radius:
                    continue

                for c in nodes:
                    if c == a or c == b:
                        continue
                    if not _has_edge(graph.network, b, c):
                        continue
                    if _has_edge(graph.network, a, c):
                        continue
                    if _distance(graph.network, b, c) > self.radius:
                        continue
                    if _distance(graph.network, a, c) > self.radius:
                        continue

                    candidates.append(Candidate(self.name, {"u": a, "v": c, "via": b}))
        return candidates

    def apply(self, graph, payload):
        new_graph = deepcopy(graph)
        u = payload["u"]
        v = payload["v"]
        if _has_edge(new_graph.network, u, v):
            return new_graph
        new_graph.add_edge(u, v, family="bar")
        return new_graph
