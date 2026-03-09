import argparse
import json
from math import sqrt
from pathlib import Path
import sys
import threading
import time

from compas.geometry import Line
from compas.geometry import Point
from compas_viewer import Viewer

# Ensure repo root and local package roots are importable when launched as a script.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
MORPH_ENGINE_ROOT = REPO_ROOT / "morph_engine"
if str(MORPH_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(MORPH_ENGINE_ROOT))

from bonobo.visual.symbols import add_force_arrow
from bonobo.visual.symbols import add_support_symbol
from morph_engine.evaluator.channels.reaction_absorption_v1 import ReactionAbsorptionChannel
from morph_engine.evaluator.evaluator import Evaluator
from morph_engine.model.structural_graph import StructuralGraph
from morph_engine.visual.style_registry import MemberStyleResolver
from morph_engine.visual.style_registry import is_graph_globally_equilibrated


def _vector_magnitude(vec3):
    return sqrt(vec3[0] * vec3[0] + vec3[1] * vec3[1] + vec3[2] * vec3[2])


def _node_xyz(graph, key):
    xyz = graph.network.node_attribute(key, "xyz") or [0.0, 0.0, 0.0]
    return [float(xyz[0]), float(xyz[1]), float(xyz[2])]


def _rounded_xyz(xyz, digits=6):
    return (round(float(xyz[0]), digits), round(float(xyz[1]), digits), round(float(xyz[2]), digits))


def _is_fixed(graph, node_key):
    fixed = graph.network.node_attribute(node_key, "fixed") or [0, 0, 0]
    if len(fixed) != 3:
        return False
    return any(float(v) != 0.0 for v in fixed)


def _add(viewer, obj, **kwargs):
    if hasattr(viewer, "add") and callable(getattr(viewer, "add")):
        return viewer.add(obj, **kwargs)
    return viewer.scene.add(obj, **kwargs)


def _update_viewer(viewer):
    if hasattr(viewer, "scene") and hasattr(viewer.scene, "update"):
        viewer.scene.update()


def clear_iteration(viewer):
    if hasattr(viewer, "clear") and callable(getattr(viewer, "clear")):
        viewer.clear()
        return
    if hasattr(viewer, "scene") and hasattr(viewer.scene, "clear"):
        viewer.scene.clear()
        return
    if hasattr(viewer, "scene") and hasattr(viewer.scene, "objects"):
        viewer.scene.objects[:] = []


def _extract_metrics_fields(payload, graph):
    metrics = payload.get("metrics", {}) if isinstance(payload, dict) else {}
    equilibrium_valid = None
    residual_magnitude = None

    if isinstance(metrics, dict):
        if "channels" in metrics:
            channel = metrics.get("channels", {}).get("global_equilibrium_v1", {})
            if isinstance(channel, dict):
                equilibrium_valid = channel.get("valid", equilibrium_valid)
                residual_magnitude = (
                    channel.get("metrics", {}).get("residual_magnitude", residual_magnitude)
                )
        equilibrium_valid = metrics.get("equilibrium_valid", equilibrium_valid)
        residual_magnitude = metrics.get("residual_magnitude", residual_magnitude)

    if equilibrium_valid is None:
        equilibrium_valid = is_graph_globally_equilibrated(graph)
    return equilibrium_valid, residual_magnitude


def _draw_metadata(viewer, graph, iteration_index, total_iterations, rule_name, equilibrium_valid, residual_magnitude):
    xyz = [_node_xyz(graph, k) for k in graph.network.nodes()]
    if xyz:
        cx = sum(p[0] for p in xyz) / len(xyz)
        cy = sum(p[1] for p in xyz) / len(xyz)
        cz = sum(p[2] for p in xyz) / len(xyz)
    else:
        cx, cy, cz = 0.0, 0.0, 0.0

    eq_text = "n/a" if equilibrium_valid is None else str(bool(equilibrium_valid))
    residual_text = "n/a" if residual_magnitude is None else "{0:.6g}".format(float(residual_magnitude))
    label = "i={0}/{1} rule={2} eq={3} residual={4}".format(
        iteration_index,
        total_iterations - 1,
        rule_name or "n/a",
        eq_text,
        residual_text,
    )
    _add(
        viewer,
        Point(cx + 0.5, cy + 0.5, cz + 0.5),
        pointsize=6,
        name=label,
        show_name=True,
        pointcolor=(1.0, 1.0, 1.0),
    )
    print(
        "Iteration {0}/{1} | rule={2} | equilibrium={3} | residual={4}".format(
            iteration_index,
            total_iterations - 1,
            rule_name or "n/a",
            eq_text,
            residual_text,
        )
    )


def _compute_reactions(graph_data):
    graph_for_reactions = StructuralGraph.from_json(graph_data)
    evaluator = Evaluator([ReactionAbsorptionChannel()])
    result = evaluator.evaluate(graph_for_reactions)
    return (
        result.get("channels", {})
        .get("reaction_absorption_v1", {})
        .get("signals", {})
        .get("reactions_by_node", {})
    )


def draw_iteration(viewer, payload):
    graph_data = payload["graph"]
    graph = StructuralGraph.from_json(graph_data)
    reactions_by_node = _compute_reactions(graph_data)
    member_style_resolver = MemberStyleResolver()

    loads_by_node = {}
    for load in graph.get_loads():
        node_key = load.get("node")
        vec = load.get("vector", [0.0, 0.0, 0.0])
        if node_key is None or len(vec) != 3:
            continue
        skey = str(node_key)
        current = loads_by_node.get(skey, [0.0, 0.0, 0.0])
        loads_by_node[skey] = [
            current[0] + float(vec[0]),
            current[1] + float(vec[1]),
            current[2] + float(vec[2]),
        ]

    seen_edges = set()
    for u, v in graph.network.edges():
        p1 = _node_xyz(graph, u)
        p2 = _node_xyz(graph, v)
        ekey = tuple(sorted([_rounded_xyz(p1), _rounded_xyz(p2)]))
        if ekey in seen_edges:
            continue
        seen_edges.add(ekey)

        style = member_style_resolver.resolve(u, v, graph)
        _add(
            viewer,
            Line(Point(*p1), Point(*p2)),
            linecolor=style["color"],
            linewidth=style.get("linewidth", 2),
            name="Member",
        )

    seen_supports = set()
    for node_key in graph.network.nodes():
        xyz = _node_xyz(graph, node_key)
        skey = str(node_key)
        pkey = _rounded_xyz(xyz)

        if _is_fixed(graph, node_key) and pkey not in seen_supports:
            seen_supports.add(pkey)
            add_support_symbol(viewer, xyz, scale=0.5)

        load_vec = loads_by_node.get(skey, [0.0, 0.0, 0.0])
        if _vector_magnitude(load_vec) > 1e-12:
            add_force_arrow(viewer, xyz, load_vec, scale=0.5, kind="load")

        reaction_vec = reactions_by_node.get(skey, [0.0, 0.0, 0.0])
        if len(reaction_vec) == 3 and _vector_magnitude(reaction_vec) > 1e-12:
            add_force_arrow(viewer, xyz, reaction_vec, scale=0.5, kind="reaction")

        temp_vec = graph.get_temp_force(node_key)
        if len(temp_vec) == 3 and _vector_magnitude(temp_vec) > 1e-12:
            add_force_arrow(viewer, xyz, temp_vec, scale=0.5, kind="temp")

        if not _is_fixed(graph, node_key):
            _add(viewer, Point(*xyz), pointcolor=(0.75, 0.75, 0.75), pointsize=6, name="Node")

    equilibrium_valid, residual_magnitude = _extract_metrics_fields(payload, graph)
    _draw_metadata(
        viewer,
        graph,
        payload["index"],
        payload["total"],
        payload.get("rule"),
        equilibrium_valid,
        residual_magnitude,
    )


def load_history(path):
    if not path.exists():
        raise FileNotFoundError("Missing history file: {0}".format(path))

    with open(path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)

    iterations = raw.get("iterations")
    if not isinstance(iterations, list) or not iterations:
        raise ValueError("Malformed history: expected non-empty list at 'iterations'.")

    normalized = []
    for idx, item in enumerate(iterations):
        if not isinstance(item, dict):
            raise ValueError("Malformed iteration at index {0}: expected object.".format(idx))

        graph_payload = None
        rule_name = None
        metrics = {}

        if "graph" in item and isinstance(item.get("graph"), dict):
            graph_payload = item["graph"]
            rule_name = item.get("rule")
            metrics = item.get("metrics", {}) if isinstance(item.get("metrics", {}), dict) else {}
        elif "nodes" in item and "edges" in item and "metadata" in item:
            graph_payload = item
        else:
            raise ValueError(
                "Malformed iteration at index {0}: expected {{'graph': ...}} or graph payload.".format(idx)
            )

        normalized.append(
            {
                "graph": graph_payload,
                "rule": rule_name,
                "metrics": metrics,
            }
        )
    return normalized


def get_iteration_payload(history, requested_index):
    total = len(history)
    clamped = max(0, min(int(requested_index), total - 1))
    payload = dict(history[clamped])
    payload["index"] = clamped
    payload["total"] = total
    payload["clamped"] = clamped != int(requested_index)
    payload["requested"] = int(requested_index)
    return payload


def _extract_key(event, *args):
    key_map = {
        32: "space",
        91: "[",
        93: "]",
        16777232: "home",
        16777233: "end",
    }
    candidates = [event] + list(args)
    for candidate in candidates:
        if candidate is None:
            continue
        if isinstance(candidate, int):
            return key_map.get(candidate)
        if isinstance(candidate, str):
            return candidate
        for attr in ("key", "text", "name", "char"):
            if not hasattr(candidate, attr):
                continue
            value = getattr(candidate, attr)
            if callable(value):
                try:
                    value = value()
                except Exception:
                    continue
            if isinstance(value, int):
                mapped = key_map.get(value)
                if mapped:
                    return mapped
            if isinstance(value, str) and value:
                return value
    return None


def _bind_keyboard(viewer, callback):
    if hasattr(viewer, "on_key_press") and callable(getattr(viewer, "on_key_press")):
        viewer.on_key_press(callback)
        return "viewer.on_key_press"

    if hasattr(viewer, "on") and callable(getattr(viewer, "on")):
        try:
            viewer.on("key_press", callback)
            return "viewer.on('key_press')"
        except Exception:
            pass

    if hasattr(viewer, "view"):
        view = viewer.view
        if hasattr(view, "on_key_press") and callable(getattr(view, "on_key_press")):
            view.on_key_press(callback)
            return "viewer.view.on_key_press"
        if hasattr(view, "on") and callable(getattr(view, "on")):
            try:
                view.on("key_press", callback)
                return "viewer.view.on('key_press')"
            except Exception:
                pass

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, default=None, help="Show a specific iteration index.")
    parser.add_argument("--play", action="store_true", help="Auto-advance iterations.")
    parser.add_argument("--fps", type=float, default=4.0, help="Playback FPS (default 4).")
    parser.add_argument("--loop", action="store_true", help="Loop playback from last to first.")
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Show latest iteration (default behavior when --step is not provided).",
    )
    args = parser.parse_args()

    history_path = REPO_ROOT / "experiments" / "last_run.json"
    try:
        history = load_history(history_path)
    except Exception as error:
        print("Could not load history: {0}".format(error))
        return

    total = len(history)
    if args.step is not None:
        start_index = args.step
    elif args.play:
        start_index = 0
    else:
        start_index = total - 1

    initial = get_iteration_payload(history, start_index)
    if initial["clamped"]:
        print(
            "Requested step {0} is out of range; clamped to {1}.".format(
                initial["requested"], initial["index"]
            )
        )

    viewer = Viewer()
    state = {
        "index": initial["index"],
        "playing": bool(args.play),
    }
    lock = threading.Lock()
    stop_event = threading.Event()

    def redraw(index):
        payload = get_iteration_payload(history, index)
        if payload["clamped"]:
            print(
                "Requested step {0} is out of range; clamped to {1}.".format(
                    payload["requested"], payload["index"]
                )
            )

        clear_iteration(viewer)
        draw_iteration(viewer, payload)
        _update_viewer(viewer)
        state["index"] = payload["index"]

    def next_iteration():
        index = state["index"] + 1
        if index >= total:
            if args.loop:
                index = 0
            else:
                index = total - 1
                state["playing"] = False
        redraw(index)

    def previous_iteration():
        index = state["index"] - 1
        if index < 0:
            index = 0
        redraw(index)

    def on_key(event=None, *extra):
        key = _extract_key(event, *extra)
        if key is None:
            return
        key_norm = key.strip().lower()
        if key_norm in ("bracketright", "]"):
            with lock:
                next_iteration()
        elif key_norm in ("bracketleft", "["):
            with lock:
                previous_iteration()
        elif key_norm in ("space", " "):
            with lock:
                state["playing"] = not state["playing"]
                print("Playback:", "ON" if state["playing"] else "OFF")
        elif key_norm == "home":
            with lock:
                redraw(0)
        elif key_norm == "end":
            with lock:
                redraw(total - 1)

    binding = _bind_keyboard(viewer, on_key)
    if binding:
        print("Keyboard controls enabled via {0}: [ ] space home end".format(binding))
    else:
        print("Keyboard controls unavailable in this compas_viewer build; using CLI controls only.")

    fps = max(0.1, float(args.fps))

    def playback_loop():
        frame_delay = 1.0 / fps
        while not stop_event.is_set():
            time.sleep(frame_delay)
            with lock:
                if not state["playing"]:
                    continue
                next_iteration()

    playback_thread = None
    if args.play:
        playback_thread = threading.Thread(target=playback_loop, daemon=True)
        playback_thread.start()

    with lock:
        redraw(state["index"])
    viewer.show()
    stop_event.set()
    if playback_thread is not None:
        playback_thread.join(timeout=0.2)


if __name__ == "__main__":
    main()
