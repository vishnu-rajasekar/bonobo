import random

from morph_engine.grammar.actions import Action
from morph_engine.grammar.operators.base import clone_graph
from morph_engine.grammar.operators.base import next_node_key
from morph_engine.grammar.operators.force_ops import get_line_of_action
from morph_engine.grammar.operators.force_ops import get_temp_force
from morph_engine.grammar.operators.node_ops import get_active_nodes


class ExtendNodeRule:
    name = "extend_node_rule"

    def __init__(self, lmin=1.0, lmax=2.0, seed=0):
        self.lmin = float(lmin)
        self.lmax = float(lmax)
        self._rng = random.Random(seed)

    def propose(self, graph):
        actions = []
        for node_key in get_active_nodes(graph, tolerance=1e-8):
            length = self._rng.uniform(self.lmin, self.lmax)
            actions.append(Action(self.name, {"node": node_key, "length": float(length)}))
        return actions

    def apply(self, graph, payload):
        node_key = payload["node"]
        new_graph = clone_graph(graph)
        loa = get_line_of_action(new_graph, node_key, tolerance=1e-12)
        if loa is None:
            return new_graph

        x, y, z = new_graph.network.node_attribute(node_key, "xyz")
        length = float(payload.get("length", (self.lmin + self.lmax) * 0.5))
        new_xyz = [
            x + length * loa["direction"][0],
            y + length * loa["direction"][1],
            z + length * loa["direction"][2],
        ]

        new_key = next_node_key(new_graph.network)
        original_force = get_temp_force(new_graph, node_key)
        new_graph.add_node(new_key, new_xyz, fixed=[0, 0, 0])
        new_graph.add_edge(node_key, new_key, family="bar")
        new_graph.set_temp_force(node_key, [0.0, 0.0, 0.0])
        new_graph.set_temp_force(new_key, original_force)
        return new_graph
