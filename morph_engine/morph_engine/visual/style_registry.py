from math import sqrt


def _safe_fixed(graph, node_key):
    fixed = graph.network.node_attribute(node_key, "fixed") or [0, 0, 0]
    if len(fixed) != 3:
        return [0, 0, 0]
    return fixed


def _is_fixed(graph, node_key):
    return any(float(v) != 0.0 for v in _safe_fixed(graph, node_key))


def _magnitude(vec3):
    return sqrt(vec3[0] * vec3[0] + vec3[1] * vec3[1] + vec3[2] * vec3[2])


def has_temp_forces(graph, eps=1e-6):
    for node_key in graph.network.nodes():
        vec = graph.get_temp_force(node_key)
        if len(vec) == 3 and _magnitude(vec) > eps:
            return True
    return False


def is_graph_globally_equilibrated(graph):
    return not has_temp_forces(graph)


def classify_member(u, v, graph):
    if _is_fixed(graph, u) or _is_fixed(graph, v):
        return "reaction"

    if is_graph_globally_equilibrated(graph) and not has_temp_forces(graph):
        return "compression"

    if has_temp_forces(graph):
        return "unknown"

    return "unknown"


class MemberStyleResolver:
    def resolve(self, u, v, graph):
        cls = classify_member(u, v, graph)

        linewidth = 4.0
        if cls == "compression":
            a = graph.network.node_attribute(u, "xyz") or [0.0, 0.0, 0.0]
            b = graph.network.node_attribute(v, "xyz") or [0.0, 0.0, 0.0]
            length = _magnitude(
                [
                    float(a[0]) - float(b[0]),
                    float(a[1]) - float(b[1]),
                    float(a[2]) - float(b[2]),
                ]
            )
            linewidth = min(6.0, max(2.0, length * 0.5))

        styles = {
            "compression": {"color": (0.0, 0.2, 1.0), "linewidth": linewidth},
            "tension": {"color": (1.0, 0.0, 0.0), "linewidth": 4.0},
            "reaction": {"color": (0.0, 0.7, 0.0), "linewidth": 4.0},
            "unknown": {"color": (0.75, 0.75, 0.75), "linewidth": 1.5},
        }
        return styles.get(cls, styles["unknown"])
