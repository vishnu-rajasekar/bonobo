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


class ExtendNode:
    name = "extend_node"

    def propose(self, graph):
        return [Candidate(self.name, {"node": node_key}) for node_key in graph.network.nodes()]

    def apply(self, graph, payload):
        new_graph = deepcopy(graph)
        node_key = payload["node"]
        xyz = list(new_graph.network.node_attribute(node_key, "xyz"))
        new_xyz = [xyz[0] + 1.0, xyz[1], xyz[2]]
        new_node = _next_node_key(new_graph.network)

        new_graph.add_node(new_node, new_xyz, fixed=[0, 0, 0])
        new_graph.add_edge(node_key, new_node, family="bar")
        return new_graph
