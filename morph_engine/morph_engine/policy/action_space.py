from morph_engine.grammar.actions import GrammarAction
from morph_engine.grammar.actions import coerce_to_grammar_action


def enumerate_applicable_actions(state, grammar, method_family="vector_gs"):
    if hasattr(grammar, "propose_actions"):
        actions = grammar.propose_actions(state, method_family=method_family)
        for action in actions:
            if not isinstance(action, GrammarAction):
                raise TypeError("Expected GrammarAction from grammar.propose_actions")
        return actions

    actions = []
    for proposed in grammar.propose(state):
        grammar_action = coerce_to_grammar_action(proposed, method_family=method_family)
        if not isinstance(grammar_action, GrammarAction):
            raise TypeError("Expected GrammarAction compatibility wrapper")
        actions.append(grammar_action)
    return actions
