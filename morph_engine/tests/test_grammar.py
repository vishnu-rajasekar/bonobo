from morph_engine.grammar.grammar_engine import GrammarEngine
from morph_engine.grammar.rules.connect_nodes import ConnectNodes
from morph_engine.grammar.rules.extend_node import ExtendNode
from morph_engine.grammar.rules.split_edge import SplitEdge
from morph_engine.model.structural_graph import StructuralGraph


def test_grammar_engine_propose_and_apply():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[1, 1, 1])
    graph.add_node("1", (1, 0, 0), fixed=[0, 0, 0])
    graph.add_edge("0", "1")

    engine = GrammarEngine([ExtendNode(), ConnectNodes(), SplitEdge()])

    candidates = engine.propose(graph)
    assert candidates

    base_nodes = graph.network.number_of_nodes()
    base_edges = graph.network.number_of_edges()
    new_graph = engine.apply(graph, candidates[0])

    new_nodes = new_graph.network.number_of_nodes()
    new_edges = new_graph.network.number_of_edges()
    assert (new_nodes != base_nodes) or (new_edges != base_edges)
