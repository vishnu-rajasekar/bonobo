"""Provisional compatibility module for a vector-GS root-link strategy.

This file remains in `grammar/rules/` for current runtime alignment and
benchmark-mode compatibility. It should be read as a method-specific
realization/strategy shim, not as a canonical top-level grammar rule intent.
"""

from morph_engine.grammar.actions import Action
from morph_engine.grammar.operators.base import clone_graph
from morph_engine.grammar.operators.base import next_node_key
from morph_engine.grammar.operators.force_ops import get_temp_force
from morph_engine.grammar.operators.force_ops import transfer_temp_force
from morph_engine.grammar.operators.node_ops import find_root_link_targets
from morph_engine.grammar.operators.node_ops import find_single_node_root_link_target
from morph_engine.semantics import create_member_force_record
from morph_engine.semantics import enrich_member_force_record
from morph_engine.semantics import set_member_force_record


class SingleNodeRootLinkRule:
    name = "single_node_root_link_rule"

    def propose(self, graph):
        targets = find_root_link_targets(graph)
        if targets:
            return [Action(self.name, target) for target in targets]

        target = find_single_node_root_link_target(graph)
        if target is None:
            return []
        return [Action(self.name, target)]

    def apply(self, graph, payload):
        new_graph = clone_graph(graph)
        source_node = payload["source_node"]
        original_force = get_temp_force(new_graph, source_node)

        if payload["target_kind"] == "support_node":
            target_node = payload["target_node"]
            new_graph.add_edge(source_node, target_node, family="bar")
            set_member_force_record(
                new_graph,
                source_node,
                target_node,
                enrich_member_force_record(
                    create_member_force_record(
                        original_force,
                        source_node=source_node,
                        target_edge=(source_node, target_node),
                        metadata={
                            "semantic_origin": "single_node_root_link",
                            "target_kind": "support_node",
                        },
                    ),
                    target_node=target_node,
                    direction_kind="compression",
                    provenance="vector_gs_support_link",
                    status="provisional",
                ),
            )
            transfer_temp_force(new_graph, source_node, target_node, clear_source=True)
            return new_graph

        target_xyz = payload["target_xyz"]
        new_node = next_node_key(new_graph.network)
        new_graph.add_node(new_node, target_xyz, fixed=[0, 0, 0])
        new_graph.add_edge(source_node, new_node, family="bar")
        set_member_force_record(
            new_graph,
            source_node,
            new_node,
            enrich_member_force_record(
                create_member_force_record(
                    original_force,
                    source_node=source_node,
                    target_edge=(source_node, new_node),
                    metadata={
                        "semantic_origin": "single_node_root_link",
                        "target_kind": payload["target_kind"],
                    },
                ),
                target_node=new_node,
                provenance="vector_gs_root_projection",
                status="provisional",
            ),
        )
        new_graph.set_temp_force(source_node, [0.0, 0.0, 0.0])
        new_graph.set_temp_force(new_node, original_force)
        return new_graph
