class GrammarEngine:
    def __init__(self, rules):
        self.rules = rules

    def propose(self, graph):
        candidates = []
        for rule in self.rules:
            candidates.extend(rule.propose(graph))
        return candidates

    def apply(self, graph, candidate):
        for rule in self.rules:
            if rule.name == candidate.rule_name:
                return rule.apply(graph, candidate.payload)
        raise ValueError("Unknown rule")
