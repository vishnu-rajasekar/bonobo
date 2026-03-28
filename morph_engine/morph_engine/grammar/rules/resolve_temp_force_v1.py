from morph_engine.grammar.actions import Action
from morph_engine.grammar.operators.base import clone_graph
from morph_engine.grammar.operators.base import next_node_key
from morph_engine.grammar.operators.force_ops import get_line_of_action
from morph_engine.grammar.operators.force_ops import get_temp_force
from morph_engine.grammar.operators.node_ops import get_active_nodes


class ResolveTempForceV1:
    name = "resolve_temp_force_v1"

    def __init__(self, step_length=2.0):
        self.step_length = step_length

    def propose(self, graph):
        return [Action(self.name, {"node": node_key}) for node_key in get_active_nodes(graph, tolerance=1e-8)]

    def apply(self, graph, payload):
        node_key = payload["node"]
        new_graph = clone_graph(graph)
        loa = get_line_of_action(new_graph, node_key)
        if loa is None:
            return new_graph

        x, y, z = new_graph.network.node_attribute(node_key, "xyz")
        new_xyz = [
            x + self.step_length * loa["direction"][0],
            y + self.step_length * loa["direction"][1],
            z + self.step_length * loa["direction"][2],
        ]

        new_key = next_node_key(new_graph.network)
        original_force = get_temp_force(new_graph, node_key)
        new_graph.add_node(new_key, new_xyz, fixed=[0, 0, 0])
        new_graph.add_edge(node_key, new_key, family="bar")
        new_graph.set_temp_force(node_key, [0, 0, 0])
        new_graph.set_temp_force(new_key, original_force)
        return new_graph
