from copy import deepcopy

from morph_engine.grammar.base import Candidate


def _next_node_key(network):
    keys = [str(k) for k in network.nodes()]
    if not keys:
        return "0"

    numeric = True
    values = []
    for key in keys:
        if key.isdigit():
            values.append(int(key))
        else:
            numeric = False
            break

    if numeric:
        return str(max(values) + 1)

    i = 0
    while True:
        candidate = "node_{0}".format(i)
        if candidate not in keys:
            return candidate
        i += 1


def _delete_edge(network, u, v):
    try:
        network.delete_edge((u, v))
        return
    except TypeError:
        pass
    network.delete_edge(u, v)


class SplitEdge:
    name = "split_edge"

    def propose(self, graph):
        return [Candidate(self.name, {"u": u, "v": v}) for u, v in graph.network.edges()]

    def apply(self, graph, payload):
        new_graph = deepcopy(graph)
        u = payload["u"]
        v = payload["v"]

        ux, uy, uz = new_graph.network.node_attribute(u, "xyz")
        vx, vy, vz = new_graph.network.node_attribute(v, "xyz")
        midpoint = [(ux + vx) * 0.5, (uy + vy) * 0.5, (uz + vz) * 0.5]
        mid_node = _next_node_key(new_graph.network)

        _delete_edge(new_graph.network, u, v)
        new_graph.add_node(mid_node, midpoint, fixed=[0, 0, 0])
        new_graph.add_edge(u, mid_node, family="bar")
        new_graph.add_edge(mid_node, v, family="bar")
        return new_graph
