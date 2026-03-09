import json
from math import sqrt
from pathlib import Path

from compas.geometry import Point, Line, Vector
from compas_viewer import Viewer

from morph_engine.model.structural_graph import StructuralGraph


# ---------------------------------------------------------
# Utility helpers (robust against internal API variations)
# ---------------------------------------------------------

def _node_keys(graph):
    return list(graph.network.nodes())


def _edge_pairs(graph):
    return list(graph.network.edges())


def _node_xyz(graph, key):
    xyz = graph.network.node_attribute(key, "xyz")
    if not xyz:
        return [0.0, 0.0, 0.0]
    return list(xyz)


def _node_fixed(graph, key):
    fixed = graph.network.node_attribute(key, "fixed")
    if not fixed or len(fixed) != 3:
        return [0, 0, 0]
    return list(fixed)


def _vector_magnitude(vec3):
    return sqrt(vec3[0] ** 2 + vec3[1] ** 2 + vec3[2] ** 2)


# ---------------------------------------------------------
# Main viewer
# ---------------------------------------------------------

def view_graph_from_json(json_path: str, load_scale: float = 0.1, force_scale: float = 0.1) -> None:

    json_path = Path(json_path)

    if not json_path.exists():
        raise FileNotFoundError(f"Graph JSON not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    graph = StructuralGraph.from_json(data)

    # -------------------------------------------------
    # Diagnostics: coincident nodes + overlapping edges
    # -------------------------------------------------

    coords = {}
    for n in _node_keys(graph):
        x, y, z = _node_xyz(graph, n)
        key = (round(x, 6), round(y, 6), round(z, 6))
        coords.setdefault(key, []).append(n)

    dup_pts = {k: v for k, v in coords.items() if len(v) > 1}

    print(
        f"nodes: {len(_node_keys(graph))}, "
        f"unique_xyz: {len(coords)}, "
        f"coincident_xyz_groups: {len(dup_pts)}"
    )

    edges_geom = set()
    dup_edges = 0

    for u, v in _edge_pairs(graph):
        a = _node_xyz(graph, u)
        b = _node_xyz(graph, v)

        ka = (round(a[0], 6), round(a[1], 6), round(a[2], 6))
        kb = (round(b[0], 6), round(b[1], 6), round(b[2], 6))

        ekey = tuple(sorted([ka, kb]))

        if ekey in edges_geom:
            dup_edges += 1

        edges_geom.add(ekey)

    print(
        f"edges: {len(_edge_pairs(graph))}, "
        f"unique_geom_edges: {len(edges_geom)}, "
        f"dup_geom_edges: {dup_edges}"
    )

    # -------------------------------------------------
    # Viewer setup
    # -------------------------------------------------

    viewer = Viewer()
    scene = viewer.scene

    # -----------------------
    # Draw nodes (deduped)
    # -----------------------

    seen_pts = set()

    for n in _node_keys(graph):
        x, y, z = _node_xyz(graph, n)
        key = (round(x, 6), round(y, 6), round(z, 6))

        if key in seen_pts:
            continue

        seen_pts.add(key)

        fixed = _node_fixed(graph, n)
        is_fixed = any(float(dof) != 0.0 for dof in fixed)

        color = (1.0, 0.0, 0.0) if is_fixed else (1.0, 1.0, 1.0)

        viewer.scene.add(Point(x, y, z), pointcolor=color, pointsize=10)

    # -----------------------
    # Draw edges (deduped)
    # -----------------------

    seen_edges = set()

    for u, v in _edge_pairs(graph):
        a = _node_xyz(graph, u)
        b = _node_xyz(graph, v)

        ka = (round(a[0], 6), round(a[1], 6), round(a[2], 6))
        kb = (round(b[0], 6), round(b[1], 6), round(b[2], 6))

        ekey = tuple(sorted([ka, kb]))

        if ekey in seen_edges:
            continue

        seen_edges.add(ekey)

        viewer.scene.add(
            Line(Point(*a), Point(*b)),
            linecolor=(0.7, 0.7, 0.7),
            linewidth=2,
        )

    # -----------------------
    # Draw external loads (blue)
    # -----------------------

    try:
        loads = graph.get_loads()
    except Exception:
        loads = []

    for load in loads:
        node_key = load.get("node")
        vec = load.get("vector", [0.0, 0.0, 0.0])

        if node_key is None or len(vec) != 3:
            continue

        start_xyz = _node_xyz(graph, node_key)

        direction = Vector(float(vec[0]), float(vec[1]), float(vec[2])) * float(load_scale)

        end_xyz = [
            start_xyz[0] + direction.x,
            start_xyz[1] + direction.y,
            start_xyz[2] + direction.z,
        ]

        viewer.scene.add(
            Line(Point(*start_xyz), Point(*end_xyz)),
            linecolor=(0.0, 0.0, 1.0),
            linewidth=3,
        )

    # -----------------------
    # Draw temp_force (orange)
    # -----------------------

    for key in _node_keys(graph):
        vec = graph.get_temp_force(key)

        if len(vec) != 3:
            continue

        if _vector_magnitude(vec) <= 1e-6:
            continue

        start_xyz = _node_xyz(graph, key)

        direction = Vector(float(vec[0]), float(vec[1]), float(vec[2])) * float(force_scale)

        end_xyz = [
            start_xyz[0] + direction.x,
            start_xyz[1] + direction.y,
            start_xyz[2] + direction.z,
        ]

        viewer.scene.add(
            Line(Point(*start_xyz), Point(*end_xyz)),
            linecolor=(1.0, 0.5, 0.0),
            linewidth=3,
        )

    viewer.show()