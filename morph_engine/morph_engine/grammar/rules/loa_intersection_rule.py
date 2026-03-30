"""Provisional compatibility module for vector-GS LOA intersection strategy.

This file remains in `grammar/rules/` to preserve current runtime imports and
benchmark/test compatibility. Architecturally, LOA intersection is treated as a
vector graphic-statics operator/strategy, not as a canonical top-level abstract
grammar rule intent.
"""

from morph_engine.grammar.actions import Action
from morph_engine.grammar.operators.base import clone_graph
from morph_engine.grammar.operators.force_ops import bidirected_ray_intersection
from morph_engine.grammar.operators.force_ops import directed_ray_intersection
from morph_engine.grammar.operators.force_ops import get_line_of_action
from morph_engine.grammar.operators.node_ops import connect_two_forces
from morph_engine.grammar.operators.node_ops import get_active_nodes


class LOAIntersectionRule:
    def __init__(self, bidirectional=False):
        self.bidirectional = bool(bidirectional)
        self.name = "bidirectional_loa_intersection_rule" if self.bidirectional else "loa_intersection_rule"

    def propose(self, graph):
        actions = []
        nodes = get_active_nodes(graph)
        intersect = bidirected_ray_intersection if self.bidirectional else directed_ray_intersection
        for index, node_a in enumerate(nodes):
            loa_a = get_line_of_action(graph, node_a)
            if loa_a is None:
                continue

            for node_b in nodes[index + 1 :]:
                loa_b = get_line_of_action(graph, node_b)
                if loa_b is None:
                    continue

                intersection = intersect(
                    loa_a["point"],
                    loa_a["direction"],
                    loa_b["point"],
                    loa_b["direction"],
                )
                if intersection is None:
                    continue
                actions.append(
                    Action(
                        self.name,
                        {
                            "node_a": node_a,
                            "node_b": node_b,
                            "intersection": intersection,
                        },
                    )
                )
        return actions

    def apply(self, graph, payload):
        connected = connect_two_forces(
            graph,
            payload["node_a"],
            payload["node_b"],
            bidirectional=self.bidirectional,
        )
        if connected is None:
            return clone_graph(graph)
        return connected
