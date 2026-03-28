from morph_engine.grammar.state_machine import GrammarState
from morph_engine.grammar.actions import coerce_to_grammar_action


class GrammarEngine:
    def __init__(self, rules):
        self.rules = rules
        self.state = GrammarState.START

    def _has_temp_forces(self, graph):
        if not hasattr(graph, "get_temp_force"):
            return False
        if not hasattr(graph, "network"):
            return False

        for node_key in graph.network.nodes():
            vec = graph.get_temp_force(node_key)
            if len(vec) != 3:
                continue
            if abs(float(vec[0])) > 1e-12 or abs(float(vec[1])) > 1e-12 or abs(float(vec[2])) > 1e-12:
                return True
        return False

    def propose(self, graph):
        candidates = self._propose_raw(graph)
        return candidates

    def propose_actions(self, graph, method_family="vector_gs"):
        return [coerce_to_grammar_action(candidate, method_family=method_family) for candidate in self._propose_raw(graph)]

    def _propose_raw(self, graph):
        if self.state == GrammarState.START:
            self.state = GrammarState.GROW

        if self.state == GrammarState.CLOSE:
            if not self._has_temp_forces(graph):
                self.state = GrammarState.END
            return []

        if self.state == GrammarState.END:
            return []

        candidates = []
        for rule in self.rules:
            candidates.extend(rule.propose(graph))

        if self.state == GrammarState.GROW and not candidates:
            self.state = GrammarState.CLOSE
            if not self._has_temp_forces(graph):
                self.state = GrammarState.END

        return candidates

    def apply(self, graph, candidate):
        for rule in self.rules:
            if rule.name == candidate.rule_name:
                return rule.apply(graph, candidate.payload)
        raise ValueError("Unknown rule")

    def apply_action(self, graph, action):
        return self.apply(graph, action)
