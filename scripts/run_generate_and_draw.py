import json

import requests

from morph_engine.grammar.grammar_engine import GrammarEngine
from morph_engine.grammar.rules.connect_nodes import ConnectNodes
from morph_engine.grammar.rules.extend_node import ExtendNode
from morph_engine.grammar.rules.split_edge import SplitEdge
from morph_engine.model.structural_graph import StructuralGraph


graph = StructuralGraph()
graph.add_node("0", (0, 0, 0), fixed=[1, 1, 1])
graph.add_node("1", (5, 0, 0), fixed=[0, 0, 0])
graph.add_edge("0", "1")

engine = GrammarEngine([ExtendNode(), ConnectNodes(), SplitEdge()])
candidates = engine.propose(graph)
new_graph = engine.apply(graph, candidates[0])

nodes_payload = {
    str(key): {"xyz": new_graph.network.node_attribute(key, "xyz")}
    for key in new_graph.network.nodes()
}
edges_payload = [[str(u), str(v)] for u, v in new_graph.network.edges()]

payload = {
    "tool": "draw_network",
    "args": {
        "nodes": nodes_payload,
        "edges": edges_payload,
    },
}

response = requests.post(
    "http://localhost:8765",
    data=json.dumps(payload),
    headers={"Content-Type": "application/json"},
)
print(response.text)
