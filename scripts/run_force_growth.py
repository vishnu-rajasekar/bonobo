import json
import time
import urllib.request

from morph_engine.evaluator.evaluator import Evaluator
from morph_engine.evaluator.channels.unbalanced_force_v1 import UnbalancedForceChannel
from morph_engine.grammar.rules.resolve_temp_force_v1 import ResolveTempForceV1
from morph_engine.model.structural_graph import StructuralGraph


MCP_URL = "http://localhost:8765"


def send_to_rhino(graph):
    nodes_payload = {
        str(node_key): {
            "xyz": graph.network.node_attribute(node_key, "xyz"),
            "temp_force": graph.get_temp_force(node_key),
        }
        for node_key in graph.network.nodes()
    }
    edges_payload = [[str(u), str(v)] for u, v in graph.network.edges()]

    payload = {
        "tool": "draw_network",
        "args": {
            "nodes": nodes_payload,
            "edges": edges_payload,
        },
    }

    try:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            MCP_URL,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as response:
            print(response.read().decode("utf-8"))
    except Exception as err:
        print("MCP error:", err)


def main():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[1, 1, 1])
    graph.set_temp_force("0", [5, 0, 0])

    evaluator = Evaluator([UnbalancedForceChannel()])
    resolve_rule = ResolveTempForceV1(step_length=2.0)

    steps = 8
    for step in range(steps):
        result = evaluator.evaluate(graph)
        global_imbalance = result["metrics"].get("global_imbalance", 0.0)
        print("step", step, "global_imbalance", global_imbalance)

        if result["signals"].get("done", False):
            print("done: imbalance below threshold")
            break

        candidates = resolve_rule.propose(graph)
        if not candidates:
            print("no candidates: stopping")
            break

        graph = resolve_rule.apply(graph, candidates[0].payload)
        send_to_rhino(graph)
        time.sleep(0.5)


if __name__ == "__main__":
    main()
