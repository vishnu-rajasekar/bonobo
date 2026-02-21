from copy import deepcopy

from morph_engine.grammar.base import Candidate


def _has_edge(network, u, v):
    try:
        return network.has_edge((u, v))
    except TypeError:
        return network.has_edge(u, v)


class ConnectNodes:
    name = "connect_nodes"

    def propose(self, graph):
        nodes = list(graph.network.nodes())
        candidates = []
        for i, u in enumerate(nodes):
            for v in nodes[i + 1 :]:
                if _has_edge(graph.network, u, v):
                    continue
                candidates.append(Candidate(self.name, {"u": u, "v": v}))
        return candidates

    def apply(self, graph, payload):
        new_graph = deepcopy(graph)
        new_graph.add_edge(payload["u"], payload["v"], family="bar")
        return new_graph
