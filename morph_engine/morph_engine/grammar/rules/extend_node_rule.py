import random

from morph_engine.grammar.actions import Action
from morph_engine.grammar.operators.base import clone_graph
from morph_engine.grammar.operators.base import next_node_key
from morph_engine.grammar.operators.node_ops import get_active_nodes
from morph_engine.semantics import build_structural_node_view
from morph_engine.semantics import create_member_force_record
from morph_engine.semantics import set_member_force_record


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
        node_view = build_structural_node_view(new_graph, node_key)
        loa = node_view.active_line_of_action
        if loa is None:
            return new_graph

        x, y, z = node_view.xyz
        length = float(payload.get("length", (self.lmin + self.lmax) * 0.5))
        new_xyz = [
            x + length * loa["direction"][0],
            y + length * loa["direction"][1],
            z + length * loa["direction"][2],
        ]

        new_key = next_node_key(new_graph.network)
        original_force = list(node_view.unresolved_force_vector)
        new_graph.add_node(new_key, new_xyz, fixed=[0, 0, 0])
        new_graph.add_edge(node_key, new_key, family="bar")
        set_member_force_record(
            new_graph,
            node_key,
            new_key,
            create_member_force_record(
                original_force,
                source_node=node_key,
                target_edge=(node_key, new_key),
                metadata={
                    "semantic_origin": "extend_node",
                    "source_node_kind": node_view.node_kind,
                    "incident_member_count_before": len(node_view.incident_member_ids),
                },
            ),
        )
        new_graph.set_temp_force(node_key, [0.0, 0.0, 0.0])
        new_graph.set_temp_force(new_key, original_force)
        return new_graph
