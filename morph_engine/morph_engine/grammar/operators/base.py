from copy import deepcopy
from dataclasses import dataclass
from math import cos
from math import sin
from math import sqrt


@dataclass(frozen=True)
class GSOperator:
    name: str
    family: str = "vector_gs"
    notes: str = ""


def clone_graph(graph):
    return deepcopy(graph)


def next_node_key(network):
    keys = [str(key) for key in network.nodes()]
    if not keys:
        return "0"

    numeric_values = []
    for key in keys:
        if not key.isdigit():
            break
        numeric_values.append(int(key))
    else:
        return str(max(numeric_values) + 1)

    index = 0
    while True:
        candidate = "node_{0}".format(index)
        if candidate not in keys:
            return candidate
        index += 1


def node_xyz(graph, key):
    xyz = graph.network.node_attribute(key, "xyz") or [0.0, 0.0, 0.0]
    return [float(xyz[0]), float(xyz[1]), float(xyz[2])]


def vector_magnitude(vec3):
    x, y, z = float(vec3[0]), float(vec3[1]), float(vec3[2])
    return sqrt(x * x + y * y + z * z)


def normalize_vector(vec3, tolerance=1e-12):
    magnitude = vector_magnitude(vec3)
    if magnitude <= tolerance:
        return None
    return [float(vec3[0]) / magnitude, float(vec3[1]) / magnitude, float(vec3[2]) / magnitude]


def rotate_z(vec3, theta):
    x, y, z = float(vec3[0]), float(vec3[1]), float(vec3[2])
    c = cos(theta)
    s = sin(theta)
    return [x * c - y * s, x * s + y * c, z]


def has_edge(network, u, v):
    try:
        return network.has_edge((u, v))
    except TypeError:
        return network.has_edge(u, v)


def edge_length(graph, u, v):
    ux, uy, uz = node_xyz(graph, u)
    vx, vy, vz = node_xyz(graph, v)
    dx = vx - ux
    dy = vy - uy
    dz = vz - uz
    return sqrt(dx * dx + dy * dy + dz * dz)
