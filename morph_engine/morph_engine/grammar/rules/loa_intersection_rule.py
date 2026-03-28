from morph_engine.grammar.actions import Action
from morph_engine.grammar.operators.base import clone_graph
from morph_engine.grammar.operators.base import next_node_key
from morph_engine.grammar.operators.force_ops import bidirected_ray_intersection
from morph_engine.grammar.operators.force_ops import directed_ray_intersection
from morph_engine.grammar.operators.force_ops import get_line_of_action
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
        new_graph = clone_graph(graph)
        node_a = payload["node_a"]
        node_b = payload["node_b"]
        new_node = next_node_key(new_graph.network)
        new_graph.add_node(new_node, payload["intersection"], fixed=[0, 0, 0])
        new_graph.add_edge(node_a, new_node, family="bar")
        new_graph.add_edge(node_b, new_node, family="bar")
        new_graph.set_temp_force(node_a, [0.0, 0.0, 0.0])
        new_graph.set_temp_force(node_b, [0.0, 0.0, 0.0])
        new_graph.set_temp_force(new_node, [0.0, 0.0, 0.0])
        return new_graph
