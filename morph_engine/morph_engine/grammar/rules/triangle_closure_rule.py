"""Provisional compatibility module for vector-GS closure strategy.

This file remains in `grammar/rules/` to preserve current imports. It is best
understood as the current vector-GS realization backing `CloseStructure`, not as
final abstract grammar truth.
"""

from morph_engine.grammar.actions import Action
from morph_engine.grammar.operators.base import clone_graph
from morph_engine.grammar.operators.base import has_edge
from morph_engine.grammar.operators.member_ops import member_length
from morph_engine.grammar.operators.node_ops import equilibrate_node
from morph_engine.semantics import build_structural_node_view
from morph_engine.semantics import create_member_force_record
from morph_engine.semantics import enrich_member_force_record
from morph_engine.semantics import set_member_force_record


class TriangleClosureRule:
    name = "triangle_closure_rule"

    def __init__(self, radius=10.0):
        self.radius = float(radius)

    def propose(self, graph):
        actions = []
        seen = set()
        for b in graph.network.nodes():
            neighbors = sorted(
                [
                    str(neighbor)
                    for neighbor in graph.network.neighbors(b)
                    if member_length(graph, b, neighbor) <= self.radius
                ]
            )
            for i, a in enumerate(neighbors):
                for c in neighbors[i + 1 :]:
                    if has_edge(graph.network, a, c):
                        continue
                    if member_length(graph, a, c) > self.radius:
                        continue
                    key = tuple(sorted((str(a), str(c), str(b))))
                    if key in seen:
                        continue
                    seen.add(key)
                    actions.append(Action(self.name, {"u": a, "v": c, "via": str(b)}))
        return actions

    def apply(self, graph, payload):
        new_graph = clone_graph(graph)
        u = payload["u"]
        v = payload["v"]
        via = payload.get("via")
        if has_edge(new_graph.network, u, v):
            return new_graph
        new_graph.add_edge(u, v, family="bar")
        closure_vector = None
        if via is not None:
            via_view = build_structural_node_view(new_graph, via)
            force_basis = via_view.non_temporary_forces or via_view.local_forces
            if force_basis:
                closure_vector = equilibrate_node(force_basis)["closing_vector"]
        if closure_vector is None:
            closure_vector = [0.0, 0.0, 0.0]
        set_member_force_record(
            new_graph,
            u,
            v,
            enrich_member_force_record(
                create_member_force_record(
                    closure_vector,
                    source_node=via,
                    target_edge=(u, v),
                    metadata={
                        "semantic_origin": "triangle_closure",
                        "via_node": None if via is None else str(via),
                    },
                ),
                target_node=v,
                provenance="vector_gs_closure",
                status="provisional",
            ),
        )
        return new_graph
