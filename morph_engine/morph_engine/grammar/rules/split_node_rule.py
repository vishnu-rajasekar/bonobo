import random

from morph_engine.grammar.actions import Action
from morph_engine.grammar.operators.base import clone_graph
from morph_engine.grammar.operators.base import next_node_key
from morph_engine.grammar.operators.base import rotate_z
from morph_engine.grammar.operators.force_ops import get_line_of_action
from morph_engine.grammar.operators.force_ops import get_temp_force
from morph_engine.grammar.operators.node_ops import get_active_nodes


class SplitNodeRule:
    name = "split_node_rule"

    def __init__(self, theta_min=0.35, theta_max=0.55, length=1.0, seed=0):
        self.theta_min = float(theta_min)
        self.theta_max = float(theta_max)
        self.length = float(length)
        self._rng = random.Random(seed)

    def propose(self, graph):
        actions = []
        for node_key in get_active_nodes(graph):
            theta = self._rng.uniform(self.theta_min, self.theta_max)
            actions.append(Action(self.name, {"node": node_key, "theta": theta}))
        return actions

    def apply(self, graph, payload):
        new_graph = clone_graph(graph)
        node_key = payload["node"]
        theta = float(payload["theta"])
        loa = get_line_of_action(new_graph, node_key)
        if loa is None:
            return new_graph

        dir_a = rotate_z(loa["direction"], theta)
        dir_b = rotate_z(loa["direction"], -theta)

        x, y, z = new_graph.network.node_attribute(node_key, "xyz")
        xyz_a = [x + self.length * dir_a[0], y + self.length * dir_a[1], z + self.length * dir_a[2]]
        xyz_b = [x + self.length * dir_b[0], y + self.length * dir_b[1], z + self.length * dir_b[2]]

        node_a = next_node_key(new_graph.network)
        new_graph.add_node(node_a, xyz_a, fixed=[0, 0, 0])
        node_b = next_node_key(new_graph.network)
        new_graph.add_node(node_b, xyz_b, fixed=[0, 0, 0])

        base_force = get_temp_force(new_graph, node_key)
        new_graph.add_edge(node_key, node_a, family="bar")
        new_graph.add_edge(node_key, node_b, family="bar")
        new_graph.set_temp_force(node_key, [0.0, 0.0, 0.0])
        new_graph.set_temp_force(node_a, base_force)
        new_graph.set_temp_force(node_b, base_force)
        return new_graph
