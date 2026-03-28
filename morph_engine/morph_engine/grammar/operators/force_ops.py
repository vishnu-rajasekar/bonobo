from .base import GSOperator
from .base import node_xyz
from .base import normalize_vector
from .base import vector_magnitude


GET_TEMP_FORCE = GSOperator("get_temp_force", notes="Read the unresolved nodal imbalance vector.")
FLIP_TEMP_FORCE_DIR = GSOperator("flip_temp_force_dir", notes="Reverse a node temp_force direction in place.")
GET_LINE_OF_ACTION = GSOperator("get_line_of_action", notes="Return point + normalized unresolved-force direction.")
TRANSFER_MEMBER_FORCE = GSOperator(
    "transfer_member_force",
    notes="Translate a member-aligned vector descriptor to a new point. Provisional until member forces are canonical.",
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
    direction = normalize_vector(get_temp_force(graph, node_key), tolerance=tolerance)
    if direction is None:
        return None
    return {
        "point": node_xyz(graph, node_key),
        "direction": direction,
    }


def transfer_member_force(graph, u, v, to_point=None):
    start = node_xyz(graph, u)
    end = node_xyz(graph, v)
    vector = [end[0] - start[0], end[1] - start[1], end[2] - start[2]]
    if to_point is None:
        translated_start = start
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
        "vector": vector,
        "magnitude": vector_magnitude(vector),
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
