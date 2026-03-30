import random

from morph_engine.grammar.actions import Action
from morph_engine.grammar.operators.base import clone_graph
from morph_engine.grammar.operators.base import next_node_key
from morph_engine.grammar.operators.base import rotate_z
from morph_engine.grammar.operators.force_ops import decompose_force_along_directions
from morph_engine.grammar.operators.node_ops import get_active_nodes
from morph_engine.semantics import build_structural_node_view
from morph_engine.semantics import create_member_force_record
from morph_engine.semantics import set_member_force_record


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
        node_view = build_structural_node_view(new_graph, node_key)
        loa = node_view.active_line_of_action
        if loa is None:
            return new_graph

        dir_a = rotate_z(loa["direction"], theta)
        dir_b = rotate_z(loa["direction"], -theta)

        x, y, z = node_view.xyz
        xyz_a = [x + self.length * dir_a[0], y + self.length * dir_a[1], z + self.length * dir_a[2]]
        xyz_b = [x + self.length * dir_b[0], y + self.length * dir_b[1], z + self.length * dir_b[2]]

        node_a = next_node_key(new_graph.network)
        new_graph.add_node(node_a, xyz_a, fixed=[0, 0, 0])
        node_b = next_node_key(new_graph.network)
        new_graph.add_node(node_b, xyz_b, fixed=[0, 0, 0])

        base_force = list(node_view.unresolved_force_vector)
        decomposed = decompose_force_along_directions(base_force, dir_a, dir_b)
        force_a = base_force if decomposed is None else decomposed["vector_a"]
        force_b = base_force if decomposed is None else decomposed["vector_b"]
        new_graph.add_edge(node_key, node_a, family="bar")
        new_graph.add_edge(node_key, node_b, family="bar")
        set_member_force_record(
            new_graph,
            node_key,
            node_a,
            create_member_force_record(
                force_a,
                source_node=node_key,
                target_edge=(node_key, node_a),
                metadata={
                    "semantic_origin": "split_node",
                    "branch": "a",
                    "theta": theta,
                    "incident_member_count_before": len(node_view.incident_member_ids),
                },
            ),
        )
        set_member_force_record(
            new_graph,
            node_key,
            node_b,
            create_member_force_record(
                force_b,
                source_node=node_key,
                target_edge=(node_key, node_b),
                metadata={
                    "semantic_origin": "split_node",
                    "branch": "b",
                    "theta": -theta,
                    "incident_member_count_before": len(node_view.incident_member_ids),
                },
            ),
        )
        new_graph.set_temp_force(node_key, [0.0, 0.0, 0.0])
        new_graph.set_temp_force(node_a, force_a)
        new_graph.set_temp_force(node_b, force_b)
        return new_graph
