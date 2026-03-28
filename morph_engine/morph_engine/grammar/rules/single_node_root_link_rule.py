from morph_engine.grammar.actions import Action
from morph_engine.grammar.operators.base import clone_graph
from morph_engine.grammar.operators.base import next_node_key
from morph_engine.grammar.operators.force_ops import get_temp_force
from morph_engine.grammar.operators.node_ops import find_single_node_root_link_target


class SingleNodeRootLinkRule:
    name = "single_node_root_link_rule"

    def propose(self, graph):
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
            current_target_force = get_temp_force(new_graph, target_node)
            new_graph.set_temp_force(source_node, [0.0, 0.0, 0.0])
            new_graph.set_temp_force(
                target_node,
                [
                    current_target_force[0] + original_force[0],
                    current_target_force[1] + original_force[1],
                    current_target_force[2] + original_force[2],
                ],
            )
            return new_graph

        target_xyz = payload["target_xyz"]
        new_node = next_node_key(new_graph.network)
        new_graph.add_node(new_node, target_xyz, fixed=[0, 0, 0])
        new_graph.add_edge(source_node, new_node, family="bar")
        new_graph.set_temp_force(source_node, [0.0, 0.0, 0.0])
        new_graph.set_temp_force(new_node, original_force)
        return new_graph
