from morph_engine.grammar.grammar_engine import GrammarEngine
from morph_engine.grammar.state_machine import GrammarState
from morph_engine.model.structural_graph import StructuralGraph


class _NoRule:
    name = "no_rule"

    def propose(self, graph):
        _ = graph
        return []

    def apply(self, graph, payload):
        _ = payload
        return graph


class _OneRule:
    name = "one_rule"

    def propose(self, graph):
        _ = graph
        return [object()]

    def apply(self, graph, payload):
        _ = payload
        return graph


def test_start_transitions_to_grow():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[0, 0, 0])

    engine = GrammarEngine([_OneRule()])
    assert engine.state == GrammarState.START

    engine.propose(graph)
    assert engine.state == GrammarState.GROW


def test_grow_transitions_to_close_when_no_rules_apply():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[0, 0, 0])
    graph.set_temp_force("0", [1, 0, 0])

    engine = GrammarEngine([_NoRule()])
    engine.state = GrammarState.GROW

    candidates = engine.propose(graph)
    assert candidates == []
    assert engine.state == GrammarState.CLOSE


def test_close_transitions_to_end_when_no_temp_forces():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[0, 0, 0])
    graph.set_temp_force("0", [0, 0, 0])

    engine = GrammarEngine([_NoRule()])
    engine.state = GrammarState.CLOSE

    candidates = engine.propose(graph)
    assert candidates == []
    assert engine.state == GrammarState.END
