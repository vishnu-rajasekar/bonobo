import json
import sys
from math import cos
from math import pi
from math import sin
from math import sqrt
from pathlib import Path
from compas.geometry import Circle, Line, Point, Frame

try:
    from compas_viewer import Viewer
except Exception as error:  # pragma: no cover - environment dependent
    Viewer = None
    VIEWER_IMPORT_ERROR = error
else:
    VIEWER_IMPORT_ERROR = None

from morph_engine.model.structural_graph import StructuralGraph
from morph_engine.visual.style_registry import MemberStyleResolver
from morph_engine.visual.style_registry import is_graph_globally_equilibrated


def _node_xyz(graph, key):
    xyz = graph.network.node_attribute(key, "xyz") or [0.0, 0.0, 0.0]
    return [float(xyz[0]), float(xyz[1]), float(xyz[2])]


def _rounded_xyz(xyz, digits=6):
    return (round(float(xyz[0]), digits), round(float(xyz[1]), digits), round(float(xyz[2]), digits))


def _vector_magnitude(vec3):
    return sqrt(vec3[0] * vec3[0] + vec3[1] * vec3[1] + vec3[2] * vec3[2])


def _load_latest_run(repo_root):
    runs_dir = repo_root / "experiments" / "runs"
    if not runs_dir.exists():
        raise FileNotFoundError("Missing runs directory: {0}".format(runs_dir))

    run_dirs = sorted([p for p in runs_dir.iterdir() if p.is_dir()])
    if not run_dirs:
        raise FileNotFoundError("No run directories found in: {0}".format(runs_dir))

    latest_run = run_dirs[-1]
    graph_json = latest_run / "final_graph.json"
    if not graph_json.exists():
        raise FileNotFoundError("Missing final_graph.json in: {0}".format(latest_run))

    metrics_json = latest_run / "metrics.json"
    summary_json = latest_run / "summary.json"
    return latest_run, graph_json, metrics_json, summary_json


def _add(viewer, obj, name=None, color=None, **kwargs):
    params = dict(kwargs)
    if color is not None:
        if isinstance(obj, Point):
            params.setdefault("pointcolor", color)
        elif isinstance(obj, Line):
            params.setdefault("linecolor", color)
        else:
            params.setdefault("color", color)
    if name is not None:
        params.setdefault("name", name)

    if hasattr(viewer, "add") and callable(getattr(viewer, "add")):
        return viewer.add(obj, **params)
    return viewer.scene.add(obj, **params)


def _is_fixed(graph, node_key):
    fixed = graph.network.node_attribute(node_key, "fixed") or [0, 0, 0]
    if len(fixed) != 3:
        return False
    return any(float(v) != 0.0 for v in fixed)


def _rotate_z(vec, angle_rad):
    c = cos(angle_rad)
    s = sin(angle_rad)
    return [vec[0] * c - vec[1] * s, vec[0] * s + vec[1] * c, vec[2]]


def _arrow_head_lines(end, unit_dir, head_len):
    back = [-unit_dir[0] * head_len, -unit_dir[1] * head_len, -unit_dir[2] * head_len]
    left = _rotate_z(back, 20.0 * pi / 180.0)
    right = _rotate_z(back, -20.0 * pi / 180.0)

    left_point = [end[0] + left[0], end[1] + left[1], end[2] + left[2]]
    right_point = [end[0] + right[0], end[1] + right[1], end[2] + right[2]]

    return (
        Line(Point(*end), Point(*left_point)),
        Line(Point(*end), Point(*right_point)),
    )


def add_support_symbol(viewer, xyz, scale=1.0):
    x, y, z = xyz

    # --- circle ---
    frame = Frame.worldXY()
    frame.point = Point(x, y, z)
    circle = Circle(0.15 * scale, frame)
    viewer.scene.add(circle, color=(0, 0, 0))

    # --- triangle ---
    p1 = Point(x - 0.4 * scale, y - 0.6 * scale, z)
    p2 = Point(x + 0.4 * scale, y - 0.6 * scale, z)
    p3 = Point(x, y, z)

    viewer.scene.add(Line(p1, p2), color=(0, 0, 0))
    viewer.scene.add(Line(p2, p3), color=(0, 0, 0))
    viewer.scene.add(Line(p3, p1), color=(0, 0, 0))
    


def add_load_arrow(viewer, xyz, vector, scale=1.0):
    mag = _vector_magnitude(vector)
    if mag <= 1e-12:
        return

    unit = [vector[0] / mag, vector[1] / mag, vector[2] / mag]
    start = [xyz[0], xyz[1], xyz[2]]
    end = [xyz[0] + unit[0] * scale, xyz[1] + unit[1] * scale, xyz[2] + unit[2] * scale]

    _add(viewer, Line(Point(*start), Point(*end)), name="Load", color=(55 / 255, 126 / 255, 227 / 255), linewidth=3)
    l1, l2 = _arrow_head_lines(end, unit, 0.15 * scale)
    _add(viewer, l1, name="Load", color=(0.0, 0.0, 1.0), linewidth=3)
    _add(viewer, l2, name="Load", color=(0.0, 0.0, 1.0), linewidth=3)


def add_reaction_arrow(viewer, xyz, vector, scale=1.0):
    mag = _vector_magnitude(vector)
    if mag <= 1e-12:
        return

    unit = [vector[0] / mag, vector[1] / mag, vector[2] / mag]
    end = [xyz[0], xyz[1], xyz[2]]
    start = [xyz[0] - unit[0] * scale, xyz[1] - unit[1] * scale, xyz[2] - unit[2] * scale]

    _add(viewer, Line(Point(*start), Point(*end)), name="Reaction", color=(0.0, 0.7, 0.0), linewidth=3)
    l1, l2 = _arrow_head_lines(end, unit, 0.15 * scale)
    _add(viewer, l1, name="Reaction", color=(0.0, 0.7, 0.0), linewidth=3)
    _add(viewer, l2, name="Reaction", color=(0.0, 0.7, 0.0), linewidth=3)


def _safe_text(viewer, position, label, color):
    # Viewer text support varies by backend; use named point as robust fallback.
    _add(viewer, Point(*position), pointsize=6, name=label, show_name=True, color=color)


def _load_json_if_exists(path):
    if path is None or not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _scene_counts(graph, loads_by_node):
    support_count = 0
    for node_key in graph.network.nodes():
        if _is_fixed(graph, node_key):
            support_count += 1
    return {
        "nodes": graph.network.number_of_nodes(),
        "edges": graph.network.number_of_edges(),
        "supports": support_count,
        "loads": len([key for key, vec in loads_by_node.items() if _vector_magnitude(vec) > 1e-12]),
    }


def _collect_frame_points(graph, loads_by_node, reactions_by_node):
    coords = []
    for node_key in graph.network.nodes():
        xyz = _node_xyz(graph, node_key)
        coords.append(xyz)

        skey = str(node_key)
        load = loads_by_node.get(skey)
        if load and _vector_magnitude(load) > 1e-12:
            mag = _vector_magnitude(load)
            unit = [load[0] / mag, load[1] / mag, load[2] / mag]
            coords.append([xyz[0] + unit[0], xyz[1] + unit[1], xyz[2] + unit[2]])

        reaction = reactions_by_node.get(skey)
        if reaction and len(reaction) == 3 and _vector_magnitude(reaction) > 1e-12:
            mag = _vector_magnitude(reaction)
            unit = [reaction[0] / mag, reaction[1] / mag, reaction[2] / mag]
            coords.append([xyz[0] + unit[0], xyz[1] + unit[1], xyz[2] + unit[2]])

    boundary = getattr(graph, "boundary", None) or {}
    if boundary.get("type") == "polygon_xy":
        for x, y in boundary.get("xy", []):
            coords.append([float(x), float(y), 0.0])
    return coords


def _frame_scene(viewer, coordinates):
    if not coordinates:
        return
    xs = [point[0] for point in coordinates]
    ys = [point[1] for point in coordinates]
    zs = [point[2] for point in coordinates]
    min_point = [min(xs), min(ys), min(zs)]
    max_point = [max(xs), max(ys), max(zs)]
    _add(viewer, Point(*min_point), name="_frame_min", color=(1.0, 1.0, 1.0), pointsize=0.1)
    _add(viewer, Point(*max_point), name="_frame_max", color=(1.0, 1.0, 1.0), pointsize=0.1)


def _print_summary(run_dir, counts, summary):
    print("run_dir:", run_dir, flush=True)
    print("nodes:", counts["nodes"], flush=True)
    print("edges:", counts["edges"], flush=True)
    print("supports:", counts["supports"], flush=True)
    print("loads:", counts["loads"], flush=True)
    if summary:
        print("termination_reason:", summary.get("termination_reason"), flush=True)
        print("iterations_executed:", summary.get("iterations_executed"), flush=True)
        print("final_residual_magnitude:", summary.get("final_residual_magnitude"), flush=True)
        print("global_equilibrium_valid:", summary.get("global_equilibrium_valid"), flush=True)


def main():
    repo_root = Path(__file__).resolve().parent.parent
    run_dir, graph_json, metrics_json, summary_json = _load_latest_run(repo_root)

    with open(graph_json, "r", encoding="utf-8") as handle:
        graph_data = json.load(handle)
    graph = StructuralGraph.from_json(graph_data)

    result = _load_json_if_exists(metrics_json)
    summary = _load_json_if_exists(summary_json)

    loads_by_node = {}
    for load in graph.get_loads() or []:
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

    reactions_by_node = (
        result.get("channels", {})
        .get("reaction_absorption_v1", {})
        .get("signals", {})
        .get("reactions_by_node", {})
    )
    counts = _scene_counts(graph, loads_by_node)
    _print_summary(run_dir, counts, summary)

    if Viewer is None:
        print("viewer_error: compas_viewer import failed: {0}".format(VIEWER_IMPORT_ERROR), file=sys.stderr)
        return 1

    member_style_resolver = MemberStyleResolver()
    viewer = Viewer()

    seen_supports = set()
    drawn_loads = set()
    drawn_reactions = set()

    for node_key in graph.network.nodes():
        xyz = _node_xyz(graph, node_key)
        pkey = _rounded_xyz(xyz)
        skey = str(node_key)

        has_load = skey in loads_by_node and _vector_magnitude(loads_by_node[skey]) > 1e-12
        has_reaction = skey in reactions_by_node and len(reactions_by_node[skey]) == 3 and _vector_magnitude(reactions_by_node[skey]) > 1e-12

        if _is_fixed(graph, node_key) and pkey not in seen_supports:
            seen_supports.add(pkey)
            add_support_symbol(viewer, xyz, scale=0.5)

        if has_load:
            lkey = (pkey, tuple(round(v, 6) for v in loads_by_node[skey]))
            if lkey not in drawn_loads:
                drawn_loads.add(lkey)
                add_load_arrow(viewer, xyz, loads_by_node[skey], scale=1.0)

        if has_reaction:
            rvec = [float(reactions_by_node[skey][0]), float(reactions_by_node[skey][1]), float(reactions_by_node[skey][2])]
            rkey = (pkey, tuple(round(v, 6) for v in rvec))
            if rkey not in drawn_reactions:
                drawn_reactions.add(rkey)
                add_reaction_arrow(viewer, xyz, rvec, scale=1.0)

        if not _is_fixed(graph, node_key) and not has_load and not has_reaction:
            _add(viewer, Point(*xyz), name="Node", color=(0.75, 0.75, 0.75), pointsize=6)

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
            name="Member",
            color=style["color"],
            linewidth=style.get("linewidth", 2),
        )

    all_xyz = [_node_xyz(graph, k) for k in graph.network.nodes()]
    if all_xyz:
        cx = sum(p[0] for p in all_xyz) / len(all_xyz)
        cy = sum(p[1] for p in all_xyz) / len(all_xyz)
        cz = sum(p[2] for p in all_xyz) / len(all_xyz)

        is_eq = is_graph_globally_equilibrated(graph)
        label = "Equilibrium: TRUE" if is_eq else "Equilibrium: FALSE"
        color = (0.0, 0.8, 0.0) if is_eq else (1.0, 0.0, 0.0)
        _safe_text(viewer, (cx + 0.5, cy + 0.5, cz + 0.5), label, color)

    _frame_scene(viewer, _collect_frame_points(graph, loads_by_node, reactions_by_node))

    try:
        viewer.show()
    except Exception as error:  # pragma: no cover - environment dependent
        print("viewer_error: {0}".format(error), file=sys.stderr)
        print("viewer_note: sparse run summary printed above; viewer failed after scene construction.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
