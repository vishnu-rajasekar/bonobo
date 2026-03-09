from copy import deepcopy

from morph_engine.grammar.base import Candidate


def _next_node_key(network):
    keys = [str(k) for k in network.nodes()]
    if not keys:
        return "0"

    numeric = True
    values = []
    for key in keys:
        if key.isdigit():
            values.append(int(key))
        else:
            numeric = False
            break

    if numeric:
        return str(max(values) + 1)

    i = 0
    while True:
        candidate = "node_{0}".format(i)
        if candidate not in keys:
            return candidate
        i += 1


def _vec_mag(vec):
    return (vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2]) ** 0.5


def _intersect_rays(p, d, q, e, eps=1e-9):
    # 2D ray intersection in XY projection.
    det = d[0] * e[1] - d[1] * e[0]
    if abs(det) < eps:
        return None

    dx = q[0] - p[0]
    dy = q[1] - p[1]

    t = (dx * e[1] - dy * e[0]) / det
    s = (dx * d[1] - dy * d[0]) / det

    if t < 0.0 or s < 0.0:
        return None

    x = p[0] + t * d[0]
    y = p[1] + t * d[1]
    z = p[2] + t * d[2]
    return [float(x), float(y), float(z)]


class LOAIntersectionRule:
    name = "loa_intersection_rule"

    def propose(self, graph):
        nodes = list(graph.network.nodes())
        candidates = []

        for i, node_a in enumerate(nodes):
            force_a = graph.get_temp_force(node_a)
            if len(force_a) != 3 or _vec_mag(force_a) <= 1e-12:
                continue

            pa = graph.network.node_attribute(node_a, "xyz") or [0.0, 0.0, 0.0]

            for node_b in nodes[i + 1 :]:
                force_b = graph.get_temp_force(node_b)
                if len(force_b) != 3 or _vec_mag(force_b) <= 1e-12:
                    continue

                pb = graph.network.node_attribute(node_b, "xyz") or [0.0, 0.0, 0.0]
                intersection = _intersect_rays(pa, force_a, pb, force_b)
                if intersection is None:
                    continue

                payload = {
                    "node_a": node_a,
                    "node_b": node_b,
                    "intersection": intersection,
                }
                candidates.append(Candidate(self.name, payload))

        return candidates

    def apply(self, graph, payload):
        new_graph = deepcopy(graph)
        node_a = payload["node_a"]
        node_b = payload["node_b"]
        intersection = payload["intersection"]

        new_node = _next_node_key(new_graph.network)
        new_graph.add_node(new_node, intersection, fixed=[0, 0, 0])
        new_graph.add_edge(node_a, new_node, family="bar")
        new_graph.add_edge(node_b, new_node, family="bar")

        new_graph.set_temp_force(node_a, [0.0, 0.0, 0.0])
        new_graph.set_temp_force(node_b, [0.0, 0.0, 0.0])
        new_graph.set_temp_force(new_node, [0.0, 0.0, 0.0])

        return new_graph
