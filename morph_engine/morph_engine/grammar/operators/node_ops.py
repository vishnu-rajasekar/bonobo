from math import atan2

from .base import GSOperator
from .base import clone_graph
from .base import has_edge
from .base import next_node_key
from .base import node_xyz
from .base import normalize_vector
from .base import vector_magnitude
from .force_ops import bidirected_ray_intersection
from .force_ops import directed_ray_intersection
from .force_ops import get_line_of_action
from .force_ops import get_temp_force


GET_ACTIVE_NODES = GSOperator("get_active_nodes", notes="List nodes carrying unresolved temp_force.")
REARRANGE_FORCES = GSOperator(
    "rearrange_forces",
    notes="Sort vectors clockwise in XY. Bonobo currently applies this as a vector utility, not persistent node force ordering.",
)
EQUILIBRATE_NODE = GSOperator(
    "equilibrate_node",
    notes="Return the closing vector needed to balance a set of vectors. Does not mutate graph semantics.",
)
TEMP_NODE_EQUILIBRIUM = GSOperator(
    "temp_node_equilibrium",
    notes="Three-way unit-vector equilibrium seed used as a vector utility only.",
)
SEARCH_CONNECTION = GSOperator(
    "search_connection",
    notes="Find nearby LOA intersections between active nodes within a search radius.",
)
CONNECT_TWO_FORCES = GSOperator(
    "connect_two_forces",
    notes="Create a new node at the intersection of two node lines of action and connect both sources.",
)
RESOLVE_TWO_FORCES = GSOperator(
    "resolve_two_forces",
    notes="If two active nodes are mutually aligned, connect them directly and clear unresolved force at both ends.",
)
SINGLE_NODE_ROOT_LINK = GSOperator(
    "find_single_node_root_link_target",
    notes="Find a benchmark-oriented support/root target for a single active unresolved front.",
)


def get_active_nodes(graph, tolerance=1e-12):
    active = []
    for node_key in graph.network.nodes():
        if vector_magnitude(get_temp_force(graph, node_key)) > tolerance:
            active.append(str(node_key))
    return active


def rearrange_forces(vectors):
    def sort_key(vec):
        angle = atan2(float(vec[1]), float(vec[0]))
        return (-angle, -vector_magnitude(vec))

    return sorted(
        [[float(vec[0]), float(vec[1]), float(vec[2])] for vec in vectors],
        key=sort_key,
    )


def equilibrate_node(vectors, tolerance=1e-12):
    total = [0.0, 0.0, 0.0]
    for vec in vectors:
        total[0] += float(vec[0])
        total[1] += float(vec[1])
        total[2] += float(vec[2])
    closing = [-total[0], -total[1], -total[2]]
    return {
        "closing_vector": closing,
        "residual_magnitude": vector_magnitude(total),
        "closed": vector_magnitude(total) <= tolerance,
    }


def temp_node_equilibrium():
    return rearrange_forces(
        [
            [0.0, -1.0, 0.0],
            [0.8660254037844386, 0.5, 0.0],
            [-0.8660254037844386, 0.5, 0.0],
        ]
    )


def _candidate_projection(graph, node_key, other_key, bidirectional=False):
    loa_a = get_line_of_action(graph, node_key)
    loa_b = get_line_of_action(graph, other_key)
    if loa_a is None or loa_b is None:
        return None

    intersect = bidirected_ray_intersection if bidirectional else directed_ray_intersection
    point = intersect(loa_a["point"], loa_a["direction"], loa_b["point"], loa_b["direction"])
    if point is None:
        return None

    point_a = node_xyz(graph, node_key)
    dx = point[0] - point_a[0]
    dy = point[1] - point_a[1]
    dz = point[2] - point_a[2]
    return {
        "node_a": str(node_key),
        "node_b": str(other_key),
        "intersection": point,
        "distance": vector_magnitude([dx, dy, dz]),
    }


def search_connection(graph, node_key, search_radius, bidirectional=False, tolerance=1e-12):
    matches = []
    if vector_magnitude(get_temp_force(graph, node_key)) <= tolerance:
        return matches

    for other_key in get_active_nodes(graph, tolerance=tolerance):
        if str(other_key) == str(node_key):
            continue
        projection = _candidate_projection(graph, node_key, other_key, bidirectional=bidirectional)
        if projection is None or projection["distance"] > float(search_radius):
            continue
        matches.append(projection)
    return sorted(matches, key=lambda item: (item["distance"], item["node_b"]))


def find_closest_projection(graph, node_key, count=1, bidirectional=False, tolerance=1e-12):
    projections = []
    origin = node_xyz(graph, node_key)
    for other_key in get_active_nodes(graph, tolerance=tolerance):
        if str(other_key) == str(node_key):
            continue
        other = node_xyz(graph, other_key)
        delta = [other[0] - origin[0], other[1] - origin[1], other[2] - origin[2]]
        projections.append((vector_magnitude(delta), str(other_key)))
    projections.sort(key=lambda item: (item[0], item[1]))

    best = None
    for _, other_key in projections[: max(1, int(count))]:
        candidate = _candidate_projection(graph, node_key, other_key, bidirectional=bidirectional)
        if candidate is None:
            continue
        if best is None or candidate["distance"] < best["distance"]:
            best = candidate
    return best


def find_closest_link(graph, node_key, tolerance=1e-12):
    return find_closest_projection(graph, node_key, count=6, bidirectional=False, tolerance=tolerance)


def connect_two_forces(graph, node_a, node_b, bidirectional=False):
    projection = _candidate_projection(graph, node_a, node_b, bidirectional=bidirectional)
    if projection is None:
        return None

    new_graph = clone_graph(graph)
    new_node = next_node_key(new_graph.network)
    new_graph.add_node(new_node, projection["intersection"], fixed=[0, 0, 0])
    new_graph.add_edge(node_a, new_node, family="bar")
    new_graph.add_edge(node_b, new_node, family="bar")
    new_graph.set_temp_force(node_a, [0.0, 0.0, 0.0])
    new_graph.set_temp_force(node_b, [0.0, 0.0, 0.0])
    new_graph.set_temp_force(new_node, [0.0, 0.0, 0.0])
    return new_graph


def connect_two_forces_direct(graph, node_a, node_b):
    return connect_two_forces(graph, node_a, node_b, bidirectional=False)


def resolve_two_forces(graph, tolerance=1e-9):
    active = get_active_nodes(graph, tolerance=tolerance)
    if len(active) != 2:
        return None

    node_a, node_b = active
    point_a = node_xyz(graph, node_a)
    point_b = node_xyz(graph, node_b)
    direction_ab = normalize_vector(
        [point_b[0] - point_a[0], point_b[1] - point_a[1], point_b[2] - point_a[2]],
        tolerance=tolerance,
    )
    loa_a = get_line_of_action(graph, node_a, tolerance=tolerance)
    loa_b = get_line_of_action(graph, node_b, tolerance=tolerance)
    if direction_ab is None or loa_a is None or loa_b is None:
        return None

    align_a = abs(
        loa_a["direction"][0] * direction_ab[0]
        + loa_a["direction"][1] * direction_ab[1]
        + loa_a["direction"][2] * direction_ab[2]
    )
    reverse_ab = [-direction_ab[0], -direction_ab[1], -direction_ab[2]]
    align_b = abs(
        loa_b["direction"][0] * reverse_ab[0]
        + loa_b["direction"][1] * reverse_ab[1]
        + loa_b["direction"][2] * reverse_ab[2]
    )
    if align_a < 1.0 - tolerance or align_b < 1.0 - tolerance:
        return None

    new_graph = clone_graph(graph)
    try:
        has_existing = new_graph.network.has_edge((node_a, node_b))
    except TypeError:
        has_existing = new_graph.network.has_edge(node_a, node_b)
    if not has_existing:
        new_graph.add_edge(node_a, node_b, family="bar")
    new_graph.set_temp_force(node_a, [0.0, 0.0, 0.0])
    new_graph.set_temp_force(node_b, [0.0, 0.0, 0.0])
    return new_graph


def _support_nodes(graph):
    return [
        str(node_key)
        for node_key in graph.network.nodes()
        if any(float(value) != 0.0 for value in (graph.network.node_attribute(node_key, "fixed") or [0, 0, 0]))
    ]


def _project_point_to_segment(point, segment_a, segment_b, tolerance=1e-12):
    ab = [
        float(segment_b[0]) - float(segment_a[0]),
        float(segment_b[1]) - float(segment_a[1]),
        float(segment_b[2]) - float(segment_a[2]),
    ]
    ap = [
        float(point[0]) - float(segment_a[0]),
        float(point[1]) - float(segment_a[1]),
        float(point[2]) - float(segment_a[2]),
    ]
    denom = ab[0] * ab[0] + ab[1] * ab[1] + ab[2] * ab[2]
    if denom <= tolerance:
        return [float(segment_a[0]), float(segment_a[1]), float(segment_a[2])]
    t = (ap[0] * ab[0] + ap[1] * ab[1] + ap[2] * ab[2]) / denom
    t = max(0.0, min(1.0, t))
    return [
        float(segment_a[0]) + t * ab[0],
        float(segment_a[1]) + t * ab[1],
        float(segment_a[2]) + t * ab[2],
    ]


def _has_node_at_xyz(graph, xyz, tolerance=1e-9):
    for node_key in graph.network.nodes():
        point = node_xyz(graph, node_key)
        delta = [point[0] - xyz[0], point[1] - xyz[1], point[2] - xyz[2]]
        if vector_magnitude(delta) <= tolerance:
            return True
    return False


def find_single_node_root_link_target(graph, tolerance=1e-9, alignment_tolerance=0.999):
    active = get_active_nodes(graph, tolerance=tolerance)
    if len(active) != 1:
        return None

    source_node = active[0]
    if graph.network.degree(source_node) <= 0:
        return None

    supports = _support_nodes(graph)
    if not supports:
        return None

    loa = get_line_of_action(graph, source_node, tolerance=tolerance)
    if loa is None:
        return None

    source_xyz = node_xyz(graph, source_node)
    best_direct = None
    for support_node in supports:
        if has_edge(graph.network, source_node, support_node):
            continue
        support_xyz = node_xyz(graph, support_node)
        direction = normalize_vector(
            [
                support_xyz[0] - source_xyz[0],
                support_xyz[1] - source_xyz[1],
                support_xyz[2] - source_xyz[2],
            ],
            tolerance=tolerance,
        )
        if direction is None:
            continue
        alignment = (
            loa["direction"][0] * direction[0]
            + loa["direction"][1] * direction[1]
            + loa["direction"][2] * direction[2]
        )
        if alignment < alignment_tolerance:
            continue
        distance = vector_magnitude(
            [
                support_xyz[0] - source_xyz[0],
                support_xyz[1] - source_xyz[1],
                support_xyz[2] - source_xyz[2],
            ]
        )
        candidate = {
            "target_kind": "support_node",
            "source_node": source_node,
            "target_node": support_node,
            "target_xyz": support_xyz,
            "alignment": alignment,
            "distance": distance,
        }
        if best_direct is None or candidate["distance"] < best_direct["distance"]:
            best_direct = candidate
    if best_direct is not None:
        return best_direct

    support_points = [(support_node, node_xyz(graph, support_node)) for support_node in supports]
    min_x = min(point[0] for _, point in support_points)
    root_side = [
        (support_node, point)
        for support_node, point in support_points
        if abs(point[0] - min_x) <= tolerance
    ]
    if len(root_side) < 2:
        return None

    root_side.sort(key=lambda item: item[1][1])
    lower_support = root_side[0]
    upper_support = root_side[-1]
    projected_xyz = _project_point_to_segment(source_xyz, lower_support[1], upper_support[1], tolerance=tolerance)
    if vector_magnitude(
        [
            projected_xyz[0] - source_xyz[0],
            projected_xyz[1] - source_xyz[1],
            projected_xyz[2] - source_xyz[2],
        ]
    ) <= tolerance:
        return None
    if _has_node_at_xyz(graph, projected_xyz, tolerance=tolerance):
        return None

    return {
        "target_kind": "root_projection",
        "source_node": source_node,
        "target_xyz": projected_xyz,
        "support_nodes": [lower_support[0], upper_support[0]],
    }
