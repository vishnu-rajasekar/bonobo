import json
from math import cos
from math import pi
from math import sin
from math import sqrt
from pathlib import Path

from compas.geometry import Circle
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Polygon
from compas_viewer import Viewer
from compas_viewer.scene import Tag

from morph_engine.model.structural_graph import StructuralGraph
from morph_engine.visual.style_registry import MemberStyleResolver
from morph_engine.visual.style_registry import is_graph_globally_equilibrated


LOAD_COLOR = (55 / 255, 126 / 255, 227 / 255)
REACTION_COLOR = (84 / 255, 165 / 255, 71 / 255)
NODE_COLOR = (0.75, 0.75, 0.75)
EXPLORED_COLOR = (0.80, 0.80, 0.80)
BOUNDARY_COLOR = (0.15, 0.15, 0.15)


def _node_xyz(graph, key):
    xyz = graph.network.node_attribute(key, "xyz") or [0.0, 0.0, 0.0]
    return [float(xyz[0]), float(xyz[1]), float(xyz[2])]


def _rounded_xyz(xyz, digits=6):
    return (round(float(xyz[0]), digits), round(float(xyz[1]), digits), round(float(xyz[2]), digits))


def _vector_magnitude(vec3):
    return sqrt(vec3[0] * vec3[0] + vec3[1] * vec3[1] + vec3[2] * vec3[2])


def _sorted_edge_key(u, v):
    su = str(u)
    sv = str(v)
    return (su, sv) if su <= sv else (sv, su)


def _load_latest_run(repo_root):
    runs_dir = repo_root / "experiments" / "runs"
    if not runs_dir.exists():
        raise FileNotFoundError("Missing runs directory: {0}".format(runs_dir))

    run_dirs = sorted([path for path in runs_dir.iterdir() if path.is_dir()])
    if not run_dirs:
        raise FileNotFoundError("No run directories found in: {0}".format(runs_dir))

    latest_run = run_dirs[-1]
    graph_json = latest_run / "final_graph.json"
    if not graph_json.exists():
        raise FileNotFoundError("Missing final_graph.json in: {0}".format(latest_run))

    metrics_json = latest_run / "metrics.json"
    trace_json = latest_run / "trace.json"
    return latest_run, graph_json, metrics_json, trace_json


def _load_json(path):
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _boundary_polygon(graph):
    support_and_load_points = []
    load_nodes = {str(load.get("node")) for load in graph.get_loads() if load.get("node") is not None}

    for node_key in graph.network.nodes():
        if not _is_fixed(graph, node_key) and str(node_key) not in load_nodes:
            continue
        xyz = _node_xyz(graph, node_key)
        support_and_load_points.append([xyz[0], xyz[1]])

    if not support_and_load_points:
        return None

    min_x = min(point[0] for point in support_and_load_points)
    max_x = max(point[0] for point in support_and_load_points)
    min_y = min(point[1] for point in support_and_load_points)
    max_y = max(point[1] for point in support_and_load_points)

    pad_x = max(0.25, 0.10 * max(1.0, max_x - min_x))
    pad_y = max(0.25, 0.10 * max(1.0, max_y - min_y))

    return Polygon(
        [
            Point(min_x - pad_x, min_y - pad_y, 0.0),
            Point(max_x + pad_x, min_y - pad_y, 0.0),
            Point(max_x + pad_x, max_y + pad_y, 0.0),
            Point(min_x - pad_x, max_y + pad_y, 0.0),
        ]
    )


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
    return any(float(value) != 0.0 for value in fixed)


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
    frame = Frame.worldXY()
    frame.point = Point(x, y, z)
    circle = Circle(0.15 * scale, frame)
    _add(viewer, circle, color=(0, 0, 0))

    p1 = Point(x - 0.4 * scale, y - 0.6 * scale, z)
    p2 = Point(x + 0.4 * scale, y - 0.6 * scale, z)
    p3 = Point(x, y, z)

    _add(viewer, Line(p1, p2), color=(0, 0, 0))
    _add(viewer, Line(p2, p3), color=(0, 0, 0))
    _add(viewer, Line(p3, p1), color=(0, 0, 0))


def add_load_arrow(viewer, xyz, vector, scale=1.0):
    mag = _vector_magnitude(vector)
    if mag <= 1e-12:
        return

    unit = [vector[0] / mag, vector[1] / mag, vector[2] / mag]
    start = [xyz[0], xyz[1], xyz[2]]
    end = [xyz[0] + unit[0] * scale, xyz[1] + unit[1] * scale, xyz[2] + unit[2] * scale]

    _add(viewer, Line(Point(*start), Point(*end)), name="Load", color=LOAD_COLOR, linewidth=3)
    l1, l2 = _arrow_head_lines(end, unit, 0.15 * scale)
    _add(viewer, l1, name="Load", color=LOAD_COLOR, linewidth=3)
    _add(viewer, l2, name="Load", color=LOAD_COLOR, linewidth=3)


def add_reaction_arrow(viewer, xyz, vector, scale=1.0, anchor_offset=None, label=None):
    mag = _vector_magnitude(vector)
    if mag <= 1e-12:
        return

    offset = anchor_offset or [0.0, 0.0, 0.0]
    unit = [vector[0] / mag, vector[1] / mag, vector[2] / mag]
    end = [xyz[0] + offset[0], xyz[1] + offset[1], xyz[2] + offset[2]]
    start = [end[0] - unit[0] * scale, end[1] - unit[1] * scale, end[2] - unit[2] * scale]

    _add(viewer, Line(Point(*start), Point(*end)), name="Reaction", color=REACTION_COLOR, linewidth=3)
    l1, l2 = _arrow_head_lines(end, unit, 0.15 * scale)
    _add(viewer, l1, name="Reaction", color=REACTION_COLOR, linewidth=3)
    _add(viewer, l2, name="Reaction", color=REACTION_COLOR, linewidth=3)
    if label:
        label_pos = [end[0] + 0.10, end[1] + 0.10, end[2]]
        _safe_text(viewer, label_pos, label, REACTION_COLOR)


def _safe_text(viewer, position, label, color):
    try:
        _add(
            viewer,
            Tag(
                text=label,
                position=position,
                color=color,
                height=28,
                absolute_height=True,
                vertical_align="bottom",
                horizontal_align="left",
            ),
            name=label,
        )
    except Exception:
        _add(viewer, Point(*position), pointsize=12, name=label, show_name=True, color=color)


def _sequence_color(step, max_step):
    if step is None or max_step <= 0:
        return (0.50, 0.50, 0.50)
    t = float(step) / float(max_step)
    return (1.0 - 0.65 * t, 0.25 + 0.55 * t, 0.20 + 0.70 * t)


def _trace_index(trace):
    node_steps = {}
    edge_steps = {}
    max_iteration = 0

    for item in trace:
        iteration = int(item.get("iteration", 0))
        if iteration > max_iteration:
            max_iteration = iteration

        for node in item.get("accepted_new_nodes", []):
            node_id = str(node.get("id"))
            if node_id:
                node_steps.setdefault(node_id, iteration)

        for edge in item.get("accepted_new_edges", []):
            if len(edge) != 2:
                continue
            edge_steps.setdefault(_sorted_edge_key(edge[0], edge[1]), iteration)

    return node_steps, edge_steps, max_iteration


def _draw_explored_geometry(viewer, trace):
    seen_segments = set()
    seen_points = set()

    for item in trace:
        iteration = int(item.get("iteration", 0))
        for geometry in item.get("candidate_geometry", []):
            for segment in geometry.get("segments", []):
                start = segment.get("start")
                end = segment.get("end")
                if start is None or end is None:
                    continue
                skey = (_rounded_xyz(start), _rounded_xyz(end))
                rkey = (_rounded_xyz(end), _rounded_xyz(start))
                if skey in seen_segments or rkey in seen_segments:
                    continue
                seen_segments.add(skey)
                _add(
                    viewer,
                    Line(Point(*start), Point(*end)),
                    name="Explored",
                    color=EXPLORED_COLOR,
                    linewidth=1,
                    opacity=0.35,
                )

            for point in geometry.get("points", []):
                xyz = point.get("xyz")
                if xyz is None:
                    continue
                pkey = _rounded_xyz(xyz)
                if pkey in seen_points:
                    continue
                seen_points.add(pkey)
                _safe_text(viewer, xyz, "c{0}".format(iteration), EXPLORED_COLOR)


def _draw_boundary(viewer, graph):
    polygon = _boundary_polygon(graph)
    if polygon is None:
        return
    points = list(polygon.points)
    for index in range(len(points)):
        start = points[index]
        end = points[(index + 1) % len(points)]
        _add(viewer, Line(start, end), name="Bounds", color=BOUNDARY_COLOR, linewidth=1)


def _draw_sequence_labels(viewer, graph, node_steps, edge_steps, max_iteration):
    for node_key in graph.network.nodes():
        step = node_steps.get(str(node_key))
        if step is None:
            continue
        xyz = _node_xyz(graph, node_key)
        label_pos = [xyz[0] + 0.20, xyz[1] + 0.20, xyz[2]]
        _safe_text(viewer, label_pos, "n{0}".format(step), _sequence_color(step, max_iteration))

    for u, v in graph.network.edges():
        step = edge_steps.get(_sorted_edge_key(u, v))
        if step is None:
            continue
        p1 = _node_xyz(graph, u)
        p2 = _node_xyz(graph, v)
        midpoint = [
            0.5 * (p1[0] + p2[0]),
            0.5 * (p1[1] + p2[1]),
            0.5 * (p1[2] + p2[2]),
        ]
        label_pos = [midpoint[0], midpoint[1] + 0.16, midpoint[2]]
        _safe_text(viewer, label_pos, "e{0}".format(step), _sequence_color(step, max_iteration))


def main():
    repo_root = Path(__file__).resolve().parent.parent
    run_dir, graph_json, metrics_json, trace_json = _load_latest_run(repo_root)

    graph = StructuralGraph.from_json(_load_json(graph_json))
    result = _load_json(metrics_json) if metrics_json.exists() else {}
    trace = _load_json(trace_json) if trace_json.exists() else []
    node_steps, edge_steps, max_iteration = _trace_index(trace)

    member_style_resolver = MemberStyleResolver()
    viewer = Viewer()

    _draw_boundary(viewer, graph)
    _draw_explored_geometry(viewer, trace)

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

    reactions_by_node = (
        result.get("channels", {})
        .get("reaction_absorption_v1", {})
        .get("signals", {})
        .get("reactions_by_node", {})
    )

    seen_supports = set()
    drawn_loads = set()
    drawn_reactions = set()

    for node_key in graph.network.nodes():
        xyz = _node_xyz(graph, node_key)
        pkey = _rounded_xyz(xyz)
        skey = str(node_key)
        node_color = _sequence_color(node_steps.get(skey), max_iteration)

        has_load = skey in loads_by_node and _vector_magnitude(loads_by_node[skey]) > 1e-12
        has_reaction = (
            skey in reactions_by_node
            and len(reactions_by_node[skey]) == 3
            and _vector_magnitude(reactions_by_node[skey]) > 1e-12
        )

        if _is_fixed(graph, node_key) and pkey not in seen_supports:
            seen_supports.add(pkey)
            add_support_symbol(viewer, xyz, scale=0.5)

        if has_load:
            lkey = (pkey, tuple(round(value, 6) for value in loads_by_node[skey]))
            if lkey not in drawn_loads:
                drawn_loads.add(lkey)
                add_load_arrow(viewer, xyz, loads_by_node[skey], scale=1.0)

        if has_reaction:
            rvec = [float(reactions_by_node[skey][0]), float(reactions_by_node[skey][1]), float(reactions_by_node[skey][2])]
            rkey = (pkey, tuple(round(value, 6) for value in rvec))
            if rkey not in drawn_reactions:
                drawn_reactions.add(rkey)
                offset = [0.22, 0.22, 0.0] if _is_fixed(graph, node_key) else [0.0, 0.0, 0.0]
                add_reaction_arrow(
                    viewer,
                    xyz,
                    rvec,
                    scale=1.0,
                    anchor_offset=offset,
                    label="R={0:.1f}".format(_vector_magnitude(rvec)),
                )

        point_color = node_color if skey in node_steps else NODE_COLOR
        if not _is_fixed(graph, node_key) and not has_load and not has_reaction:
            _add(viewer, Point(*xyz), name="Node", color=point_color, pointsize=8)

    seen_edges = set()
    for u, v in graph.network.edges():
        p1 = _node_xyz(graph, u)
        p2 = _node_xyz(graph, v)
        ekey = tuple(sorted([_rounded_xyz(p1), _rounded_xyz(p2)]))
        if ekey in seen_edges:
            continue
        seen_edges.add(ekey)

        style = member_style_resolver.resolve(u, v, graph)
        step = edge_steps.get(_sorted_edge_key(u, v))
        edge_color = _sequence_color(step, max_iteration) if step is not None else style["color"]
        _add(
            viewer,
            Line(Point(*p1), Point(*p2)),
            name="Member",
            color=edge_color,
            linewidth=max(style.get("linewidth", 2), 3 if step is not None else 2),
        )

    _draw_sequence_labels(viewer, graph, node_steps, edge_steps, max_iteration)

    all_xyz = [_node_xyz(graph, key) for key in graph.network.nodes()]
    if all_xyz:
        cx = sum(point[0] for point in all_xyz) / len(all_xyz)
        cy = sum(point[1] for point in all_xyz) / len(all_xyz)
        cz = sum(point[2] for point in all_xyz) / len(all_xyz)

        is_eq = is_graph_globally_equilibrated(graph)
        eq_label = "Equilibrium: TRUE" if is_eq else "Equilibrium: FALSE"
        eq_color = (0.0, 0.8, 0.0) if is_eq else (1.0, 0.0, 0.0)
        _safe_text(viewer, (cx + 0.5, cy + 0.5, cz + 0.5), eq_label, eq_color)
        _safe_text(viewer, (cx + 0.5, cy + 0.2, cz + 0.5), "Run: {0}".format(run_dir.name), (0.1, 0.1, 0.1))
        _safe_text(viewer, (cx + 0.5, cy - 0.1, cz + 0.5), "Sequence labels: n<step>, e<step>, c<iter>", (0.1, 0.1, 0.1))

    viewer.show()


if __name__ == "__main__":
    main()
