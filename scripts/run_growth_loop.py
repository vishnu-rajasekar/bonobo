import json
import time
import urllib.request

from morph_engine.model.structural_graph import StructuralGraph
from morph_engine.grammar.grammar_engine import GrammarEngine
from morph_engine.grammar.rules.extend_node import ExtendNode
from morph_engine.grammar.rules.connect_nodes import ConnectNodes
from morph_engine.grammar.rules.split_edge import SplitEdge


MCP_URL = "http://localhost:8765"


def send_to_rhino(graph):
    nodes_payload = {
        str(k): {"xyz": graph.network.node_attribute(k, "xyz")}
        for k in graph.network.nodes()
    }

    edges_payload = [
        [str(u), str(v)]
        for u, v in graph.network.edges()
    ]

    payload = {
        "tool": "draw_network",
        "args": {
            "nodes": nodes_payload,
            "edges": edges_payload
        }
    }

    req = urllib.request.Request(
        MCP_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req) as response:
        print(response.read().decode())


# ---- Base graph ----
g = StructuralGraph()
g.add_node("0", (0, 0, 0), fixed=[1, 1, 1])
g.add_node("1", (5, 0, 0), fixed=[0, 0, 0])
g.add_edge("0", "1", family="bar")

engine = GrammarEngine([
    ExtendNode(),
    ConnectNodes(),
    SplitEdge()
])

# ---- Growth loop ----
steps = 8

for i in range(steps):
    print(f"Step {i+1}")

    candidates = engine.propose(g)
    if not candidates:
        print("No candidates available.")
        break

    # deterministic: pick first candidate
    candidate = candidates[0]

    g = engine.apply(g, candidate)

    send_to_rhino(g)

    time.sleep(1)
