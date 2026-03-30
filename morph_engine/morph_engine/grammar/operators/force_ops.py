from .base import GSOperator
from .base import node_xyz
from .base import normalize_vector
from .base import vector_magnitude
from morph_engine.semantics import build_structural_node_view
from morph_engine.semantics import build_structural_member_view


GET_TEMP_FORCE = GSOperator("get_temp_force", notes="Read the unresolved nodal imbalance vector.")
FLIP_TEMP_FORCE_DIR = GSOperator("flip_temp_force_dir", notes="Reverse a node temp_force direction in place.")
GET_LINE_OF_ACTION = GSOperator("get_line_of_action", notes="Return point + normalized unresolved-force direction.")
TRANSFER_MEMBER_FORCE = GSOperator(
    "transfer_member_force",
    notes="Translate a member-aligned vector descriptor to a new point. Provisional until member forces are canonical.",
)
TRANSFER_TEMP_FORCE = GSOperator(
    "transfer_temp_force",
    notes="Move unresolved temp_force from one node to another, combining with any existing unresolved force at the target.",
)
DECOMPOSE_FORCE_ALONG_DIRECTIONS = GSOperator(
    "decompose_force_along_directions",
    notes="Resolve one planar force vector into two branch-aligned vectors. Provisional vector GS split utility.",
)


def get_temp_force(graph, node_key):
    return [float(value) for value in graph.get_temp_force(node_key)]


def reverse_force(force_vector):
    return [-float(force_vector[0]), -float(force_vector[1]), -float(force_vector[2])]


def flip_temp_force_dir(graph, node_key):
    flipped = reverse_force(get_temp_force(graph, node_key))
    graph.set_temp_force(node_key, flipped)
    return flipped


def get_line_of_action(graph, node_key, tolerance=1e-12):
    node_view = build_structural_node_view(graph, node_key)
    loa = node_view.active_line_of_action
    if loa is None:
        return None
    return loa


def transfer_member_force(graph, u, v, to_point=None):
    member_view = build_structural_member_view(graph, (u, v))
    record = member_view.force_record or {}
    vector = record.get("vector")
    if vector is None:
        start = node_xyz(graph, u)
        end = node_xyz(graph, v)
        vector = [end[0] - start[0], end[1] - start[1], end[2] - start[2]]
    if to_point is None:
        translated_start = node_xyz(graph, u)
    else:
        translated_start = [float(to_point[0]), float(to_point[1]), float(to_point[2])]
    translated_end = [
        translated_start[0] + vector[0],
        translated_start[1] + vector[1],
        translated_start[2] + vector[2],
    ]
    return {
        "member": [str(u), str(v)],
        "start": translated_start,
        "end": translated_end,
        "vector": [float(vector[0]), float(vector[1]), float(vector[2])],
        "magnitude": vector_magnitude(vector),
        "force_record": dict(record),
    }


def transfer_temp_force(graph, source_node, target_node, clear_source=True):
    source = get_temp_force(graph, source_node)
    target = get_temp_force(graph, target_node)
    combined = [
        float(target[0]) + float(source[0]),
        float(target[1]) + float(source[1]),
        float(target[2]) + float(source[2]),
    ]
    graph.set_temp_force(target_node, combined)
    if clear_source:
        graph.set_temp_force(source_node, [0.0, 0.0, 0.0])
    return combined


def decompose_force_along_directions(force_vector, direction_a, direction_b, tolerance=1e-12):
    fx = float(force_vector[0])
    fy = float(force_vector[1])
    det = float(direction_a[0]) * float(direction_b[1]) - float(direction_a[1]) * float(direction_b[0])
    if abs(det) <= tolerance:
        return None

    scale_a = (fx * float(direction_b[1]) - fy * float(direction_b[0])) / det
    scale_b = (fy * float(direction_a[0]) - fx * float(direction_a[1])) / det
    vector_a = [
        scale_a * float(direction_a[0]),
        scale_a * float(direction_a[1]),
        scale_a * float(direction_a[2]),
    ]
    vector_b = [
        scale_b * float(direction_b[0]),
        scale_b * float(direction_b[1]),
        scale_b * float(direction_b[2]),
    ]
    return {
        "scale_a": scale_a,
        "scale_b": scale_b,
        "vector_a": vector_a,
        "vector_b": vector_b,
    }


def directed_ray_intersection(point_a, vector_a, point_b, vector_b, eps=1e-9):
    det = float(vector_a[0]) * float(vector_b[1]) - float(vector_a[1]) * float(vector_b[0])
    if abs(det) < eps:
        return None

    dx = float(point_b[0]) - float(point_a[0])
    dy = float(point_b[1]) - float(point_a[1])
    ta = (dx * float(vector_b[1]) - dy * float(vector_b[0])) / det
    tb = (dx * float(vector_a[1]) - dy * float(vector_a[0])) / det
    if ta < 0.0 or tb < 0.0:
        return None

    return [
        float(point_a[0]) + ta * float(vector_a[0]),
        float(point_a[1]) + ta * float(vector_a[1]),
        float(point_a[2]) + ta * float(vector_a[2]),
    ]


def bidirected_ray_intersection(point_a, vector_a, point_b, vector_b, eps=1e-9):
    det = float(vector_a[0]) * float(vector_b[1]) - float(vector_a[1]) * float(vector_b[0])
    if abs(det) < eps:
        return None

    dx = float(point_b[0]) - float(point_a[0])
    dy = float(point_b[1]) - float(point_a[1])
    ta = (dx * float(vector_b[1]) - dy * float(vector_b[0])) / det
    return [
        float(point_a[0]) + ta * float(vector_a[0]),
        float(point_a[1]) + ta * float(vector_a[1]),
        float(point_a[2]) + ta * float(vector_a[2]),
    ]
