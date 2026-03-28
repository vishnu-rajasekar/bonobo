from morph_engine.grammar.actions import Action
from morph_engine.grammar.operators.base import clone_graph
from morph_engine.grammar.operators.base import has_edge
from morph_engine.grammar.operators.member_ops import member_length


class TriangleClosureRule:
    name = "triangle_closure_rule"

    def __init__(self, radius=10.0):
        self.radius = float(radius)

    def propose(self, graph):
        actions = []
        nodes = list(graph.network.nodes())
        for i, a in enumerate(nodes):
            for j in range(i + 1, len(nodes)):
                b = nodes[j]
                if not has_edge(graph.network, a, b):
                    continue
                if member_length(graph, a, b) > self.radius:
                    continue

                for c in nodes:
                    if c == a or c == b:
                        continue
                    if not has_edge(graph.network, b, c):
                        continue
                    if has_edge(graph.network, a, c):
                        continue
                    if member_length(graph, b, c) > self.radius:
                        continue
                    if member_length(graph, a, c) > self.radius:
                        continue
                    actions.append(Action(self.name, {"u": a, "v": c, "via": b}))
        return actions

    def apply(self, graph, payload):
        new_graph = clone_graph(graph)
        u = payload["u"]
        v = payload["v"]
        if has_edge(new_graph.network, u, v):
            return new_graph
        new_graph.add_edge(u, v, family="bar")
        return new_graph
