import random

from morph_engine.grammar.actions import Action
from morph_engine.grammar.operators.base import clone_graph
from morph_engine.grammar.operators.base import next_node_key
from morph_engine.grammar.operators.base import rotate_z
from morph_engine.grammar.operators.node_ops import get_active_nodes
from morph_engine.semantics import build_structural_node_view


class CreateNodeRule:
    name = "create_node_rule"

    def __init__(self, lmin=1.5, lmax=3.0, angle_min=-0.2, angle_max=0.2, seed=0):
        self.lmin = float(lmin)
        self.lmax = float(lmax)
        self.angle_min = float(angle_min)
        self.angle_max = float(angle_max)
        self._rng = random.Random(seed)

    def propose(self, graph):
        actions = []
        for node_key in get_active_nodes(graph, tolerance=1e-8):
            node_view = build_structural_node_view(graph, node_key)
            if node_view.degree > 0:
                continue
            length = self._rng.uniform(self.lmin, self.lmax)
            angle = self._rng.uniform(self.angle_min, self.angle_max)
            actions.append(
                Action(
                    self.name,
                    {
                        "node": str(node_key),
                        "length": float(length),
                        "angle": float(angle),
                    },
                )
            )
        return actions

    def apply(self, graph, payload):
        node_key = payload["node"]
        new_graph = clone_graph(graph)
        node_view = build_structural_node_view(new_graph, node_key)
        loa = node_view.active_line_of_action
        if loa is None:
            return new_graph

        length = float(payload.get("length", (self.lmin + self.lmax) * 0.5))
        angle = float(payload.get("angle", 0.0))
        direction = rotate_z(loa["direction"], angle)
        xyz = node_view.xyz
        new_xyz = [
            xyz[0] + length * direction[0],
            xyz[1] + length * direction[1],
            xyz[2] + length * direction[2],
        ]
        new_key = next_node_key(new_graph.network)
        new_graph.add_node(
            new_key,
            new_xyz,
            fixed=[0, 0, 0],
            attributes={
                "semantic_role": "floating_seed",
                "seed_from": str(node_key),
            },
        )
        new_graph.add_force_to_node(
            new_key,
            {
                "kind": "temporary",
                "vector": list(node_view.unresolved_force_vector),
                "source_node": str(node_key),
                "status": "provisional",
                "provenance": "create_node_seed",
                "metadata": {
                    "semantic_origin": "create_node",
                    "seed_parent": str(node_key),
                    "seed_angle": angle,
                },
            },
        )
        return new_graph
