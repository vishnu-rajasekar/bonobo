from morph_engine.grammar.actions import Action
from morph_engine.grammar.operators.base import clone_graph
from morph_engine.grammar.operators.node_ops import get_active_nodes
from morph_engine.grammar.operators.node_ops import resolve_two_forces


class ResolveTwoForcesRule:
    name = "resolve_two_forces_rule"

    def propose(self, graph):
        active = get_active_nodes(graph)
        if len(active) != 2:
            return []
        if resolve_two_forces(graph) is None:
            return []
        return [Action(self.name, {"node_a": active[0], "node_b": active[1]})]

    def apply(self, graph, payload):
        resolved = resolve_two_forces(graph)
        if resolved is None:
            return clone_graph(graph)
        return resolved
