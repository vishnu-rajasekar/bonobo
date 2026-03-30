import hashlib
import json
from math import cos
from math import sin
from math import sqrt


def _node_keys(graph):
    return sorted([str(key) for key in graph.network.nodes()], key=lambda item: (len(item), item))


def _edge_pairs(graph):
    edges = []
    for u, v in graph.network.edges():
        su = str(u)
        sv = str(v)
        if su <= sv:
            edges.append((su, sv))
        else:
            edges.append((sv, su))
    return sorted(edges)


def _adjacency(graph):
    adjacency = {key: set() for key in _node_keys(graph)}
    for u, v in _edge_pairs(graph):
        adjacency[u].add(v)
        adjacency[v].add(u)
    return adjacency


def _node_xyz(graph, key):
    xyz = graph.network.node_attribute(key, "xyz") or [0.0, 0.0, 0.0]
    return [float(xyz[0]), float(xyz[1]), float(xyz[2])]


def _temp_force(graph, key):
    vec = graph.get_temp_force(key)
    return [float(vec[0]), float(vec[1]), float(vec[2])]


def _fixed(graph, key):
    fixed = graph.network.node_attribute(key, "fixed") or [0, 0, 0]
    return [int(fixed[0]), int(fixed[1]), int(fixed[2])]


def _vector_magnitude(vec3):
    return sqrt(vec3[0] * vec3[0] + vec3[1] * vec3[1] + vec3[2] * vec3[2])


def _normalize(vec3):
    mag = _vector_magnitude(vec3)
    if mag <= 1e-12:
        return None
    return [vec3[0] / mag, vec3[1] / mag, vec3[2] / mag]


def _rotate_z(vec3, theta):
    c = cos(theta)
    s = sin(theta)
    return [vec3[0] * c - vec3[1] * s, vec3[0] * s + vec3[1] * c, vec3[2]]


def count_temp_force_nodes(graph, eps=1e-12):
    count = 0
    for key in graph.network.nodes():
        if _vector_magnitude(_temp_force(graph, key)) > eps:
            count += 1
    return count


def total_temp_force_magnitude(graph, eps=1e-12):
    total = 0.0
    for key in graph.network.nodes():
        magnitude = _vector_magnitude(_temp_force(graph, key))
        if magnitude > eps:
            total += magnitude
    return total


def graph_state_id(graph):
    payload = json.dumps(graph.to_json(), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha1(payload).hexdigest()[:12]


def graph_counts(graph):
    return {
        "node_count": len(list(graph.network.nodes())),
        "edge_count": len(list(graph.network.edges())),
        "temp_force_count": count_temp_force_nodes(graph),
        "total_temp_force_magnitude": total_temp_force_magnitude(graph),
    }


def support_node_ids(graph):
    supports = []
    for key in _node_keys(graph):
        if any(_fixed(graph, key)):
            supports.append(key)
    return supports


def bounds_contains_xy(bounds, xy, eps=1e-9):
    return (
        float(bounds["min"][0]) - eps <= float(xy[0]) <= float(bounds["max"][0]) + eps
        and float(bounds["min"][1]) - eps <= float(xy[1]) <= float(bounds["max"][1]) + eps
    )


def bounds_contains_graph(graph, bounds, eps=1e-9):
    outside_nodes = []
    outside_edges = []

    for key in _node_keys(graph):
        xyz = _node_xyz(graph, key)
        if not bounds_contains_xy(bounds, xyz[:2], eps=eps):
            outside_nodes.append(key)

    for u, v in _edge_pairs(graph):
        if u in outside_nodes or v in outside_nodes:
            outside_edges.append([u, v])

    return {
        "inside_bounds": len(outside_nodes) == 0 and len(outside_edges) == 0,
        "outside_node_ids": outside_nodes,
        "outside_edge_ids": outside_edges,
    }


def accepted_graph_digest(graph):
    nodes = []
    for key in _node_keys(graph):
        nodes.append(
            {
                "id": key,
                "xyz": _node_xyz(graph, key),
                "fixed": _fixed(graph, key),
                "temp_force": _temp_force(graph, key),
            }
        )

    edges = []
    for u, v in _edge_pairs(graph):
        xyz_u = _node_xyz(graph, u)
        xyz_v = _node_xyz(graph, v)
        dx = xyz_v[0] - xyz_u[0]
        dy = xyz_v[1] - xyz_u[1]
        dz = xyz_v[2] - xyz_u[2]
        edges.append(
            {
                "u": u,
                "v": v,
                "length": sqrt(dx * dx + dy * dy + dz * dz),
            }
        )

    return {
        "state_id": graph_state_id(graph),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "bounding_box": _bounding_box(graph),
    }


def _bounding_box(graph):
    points = [_node_xyz(graph, key) for key in _node_keys(graph)]
    if not points:
        return {
            "min": [0.0, 0.0, 0.0],
            "max": [0.0, 0.0, 0.0],
        }
    return {
        "min": [min(point[i] for point in points) for i in range(3)],
        "max": [max(point[i] for point in points) for i in range(3)],
    }


def _node_degree_map(graph):
    degree_map = {}
    for key in _node_keys(graph):
        degree_map[key] = int(graph.network.degree(key))
    return degree_map


def _degree_histogram(graph):
    histogram = {}
    for degree in _node_degree_map(graph).values():
        bucket = str(degree)
        histogram[bucket] = histogram.get(bucket, 0) + 1
    return histogram


def _connected_component_count(graph):
    adjacency = _adjacency(graph)

    seen = set()
    count = 0
    for start in adjacency:
        if start in seen:
            continue
        count += 1
        stack = [start]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(sorted(adjacency[current] - seen))
    return count


def _load_node_ids(graph):
    return sorted({str(load.get("node")) for load in graph.get_loads() if load.get("node") is not None})


def _two_member_non_collinear_joints(graph, tolerance=1e-6, alignment_tolerance=0.999):
    load_nodes = set(_load_node_ids(graph))
    suspicious = []

    for key in _node_keys(graph):
        if key in load_nodes:
            continue
        if any(_fixed(graph, key)):
            continue
        if _vector_magnitude(_temp_force(graph, key)) > tolerance:
            continue

        neighbors = sorted(_adjacency(graph)[key])
        if len(neighbors) != 2:
            continue

        origin = _node_xyz(graph, key)
        vec_a = _normalize(
            [
                _node_xyz(graph, neighbors[0])[0] - origin[0],
                _node_xyz(graph, neighbors[0])[1] - origin[1],
                _node_xyz(graph, neighbors[0])[2] - origin[2],
            ]
        )
        vec_b = _normalize(
            [
                _node_xyz(graph, neighbors[1])[0] - origin[0],
                _node_xyz(graph, neighbors[1])[1] - origin[1],
                _node_xyz(graph, neighbors[1])[2] - origin[2],
            ]
        )
        if vec_a is None or vec_b is None:
            continue

        alignment = abs(vec_a[0] * vec_b[0] + vec_a[1] * vec_b[1] + vec_a[2] * vec_b[2])
        if alignment >= alignment_tolerance:
            continue

        suspicious.append(
            {
                "node_id": key,
                "xyz": origin,
                "incident_neighbors": neighbors,
                "abs_alignment": alignment,
            }
        )

    return suspicious


def _duplicate_nodes(graph, tolerance):
    nodes = _node_keys(graph)
    duplicates = []
    for i, u in enumerate(nodes):
        pu = _node_xyz(graph, u)
        for v in nodes[i + 1 :]:
            pv = _node_xyz(graph, v)
            dx = pv[0] - pu[0]
            dy = pv[1] - pu[1]
            dz = pv[2] - pu[2]
            distance = sqrt(dx * dx + dy * dy + dz * dz)
            if distance <= tolerance:
                duplicates.append({"u": u, "v": v, "distance": distance})
    return duplicates


def _duplicate_edges(graph):
    seen = {}
    duplicates = []
    for u, v in _edge_pairs(graph):
        key = (u, v)
        seen[key] = seen.get(key, 0) + 1
    for key, count in seen.items():
        if count > 1:
            duplicates.append({"u": key[0], "v": key[1], "count": count})
    return duplicates


def _orientation(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _shares_endpoint(edge_a, edge_b):
    return edge_a[0] in edge_b or edge_a[1] in edge_b


def _projection_overlap(a0, a1, b0, b1, eps):
    left = max(min(a0, a1), min(b0, b1))
    right = min(max(a0, a1), max(b0, b1))
    return (right - left) > eps


def _segments_overlap(p1, p2, q1, q2, eps):
    o1 = _orientation(p1, p2, q1)
    o2 = _orientation(p1, p2, q2)
    if abs(o1) > eps or abs(o2) > eps:
        return False

    if abs(p1[0] - p2[0]) >= abs(p1[1] - p2[1]):
        return _projection_overlap(p1[0], p2[0], q1[0], q2[0], eps)
    return _projection_overlap(p1[1], p2[1], q1[1], q2[1], eps)


def _segments_cross(p1, p2, q1, q2, eps):
    o1 = _orientation(p1, p2, q1)
    o2 = _orientation(p1, p2, q2)
    o3 = _orientation(q1, q2, p1)
    o4 = _orientation(q1, q2, p2)

    if abs(o1) <= eps or abs(o2) <= eps or abs(o3) <= eps or abs(o4) <= eps:
        return False

    return (o1 > 0.0) != (o2 > 0.0) and (o3 > 0.0) != (o4 > 0.0)


def _minimum_node_distance(graph):
    nodes = _node_keys(graph)
    if len(nodes) < 2:
        return 0.0

    minimum = None
    for i, u in enumerate(nodes):
        pu = _node_xyz(graph, u)
        for v in nodes[i + 1 :]:
            pv = _node_xyz(graph, v)
            dx = pv[0] - pu[0]
            dy = pv[1] - pu[1]
            dz = pv[2] - pu[2]
            distance = sqrt(dx * dx + dy * dy + dz * dz)
            if minimum is None or distance < minimum:
                minimum = distance
    return 0.0 if minimum is None else minimum


def _triangle_count(graph):
    adjacency = _adjacency(graph)

    count = 0
    nodes = _node_keys(graph)
    for i, a in enumerate(nodes):
        for j in range(i + 1, len(nodes)):
            b = nodes[j]
            if b not in adjacency[a]:
                continue
            for c in nodes[j + 1 :]:
                if c in adjacency[a] and c in adjacency[b]:
                    count += 1
    return count


def extract_graph_descriptors(graph, tolerance=1e-6):
    edge_lengths = []
    edge_direction_vectors = []
    overlapping_edges = []
    crossing_edges = []
    edge_records = _edge_pairs(graph)

    for u, v in edge_records:
        p1 = _node_xyz(graph, u)
        p2 = _node_xyz(graph, v)
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dz = p2[2] - p1[2]
        length = sqrt(dx * dx + dy * dy + dz * dz)
        edge_lengths.append({"u": u, "v": v, "length": length})
        edge_direction_vectors.append({"u": u, "v": v, "direction": [dx, dy, dz]})

    for i, edge_a in enumerate(edge_records):
        p1 = _node_xyz(graph, edge_a[0])
        p2 = _node_xyz(graph, edge_a[1])
        for edge_b in edge_records[i + 1 :]:
            if _shares_endpoint(edge_a, edge_b):
                continue
            q1 = _node_xyz(graph, edge_b[0])
            q2 = _node_xyz(graph, edge_b[1])

            if _segments_overlap(p1, p2, q1, q2, tolerance):
                overlapping_edges.append(
                    {"edge_a": [edge_a[0], edge_a[1]], "edge_b": [edge_b[0], edge_b[1]]}
                )
            elif _segments_cross(p1, p2, q1, q2, tolerance):
                crossing_edges.append(
                    {"edge_a": [edge_a[0], edge_a[1]], "edge_b": [edge_b[0], edge_b[1]]}
                )

    return {
        "node_coordinates": {key: _node_xyz(graph, key) for key in _node_keys(graph)},
        "edge_endpoint_ids": [[u, v] for u, v in edge_records],
        "edge_lengths": edge_lengths,
        "edge_direction_vectors": edge_direction_vectors,
        "node_degree_histogram": _degree_histogram(graph),
        "connected_component_count": _connected_component_count(graph),
        "duplicate_nodes": _duplicate_nodes(graph, tolerance),
        "duplicate_node_count": len(_duplicate_nodes(graph, tolerance)),
        "duplicate_edges": _duplicate_edges(graph),
        "duplicate_edge_count": len(_duplicate_edges(graph)),
        "overlapping_edges": overlapping_edges,
        "overlapping_edge_count": len(overlapping_edges),
        "crossing_edges": crossing_edges,
        "crossing_edge_count": len(crossing_edges),
        "minimum_node_distance": _minimum_node_distance(graph),
        "triangle_count": _triangle_count(graph),
        "bounding_box": _bounding_box(graph),
    }


def support_distance_metrics(graph, tolerance=1e-6):
    supports = support_node_ids(graph)
    active_nodes = [key for key in _node_keys(graph) if _vector_magnitude(_temp_force(graph, key)) > tolerance]

    if not supports:
        return {
            "active_temp_force_node_ids": active_nodes,
            "nearest_support_distance": None,
            "nearest_support_hops": None,
            "support_reachable_path_count": 0,
        }

    adjacency = _adjacency(graph)
    min_distance = None
    min_hops = None
    reachable_count = 0

    for node in active_nodes:
        point = _node_xyz(graph, node)
        node_min_distance = min(
            sqrt(
                (_node_xyz(graph, support)[0] - point[0]) ** 2
                + (_node_xyz(graph, support)[1] - point[1]) ** 2
                + (_node_xyz(graph, support)[2] - point[2]) ** 2
            )
            for support in supports
        )
        if min_distance is None or node_min_distance < min_distance:
            min_distance = node_min_distance

        hops = _nearest_support_hops(node, supports, adjacency)
        if hops is not None:
            reachable_count += 1
            if min_hops is None or hops < min_hops:
                min_hops = hops

    return {
        "active_temp_force_node_ids": active_nodes,
        "nearest_support_distance": min_distance,
        "nearest_support_hops": min_hops,
        "support_reachable_path_count": reachable_count,
    }


def _nearest_support_hops(start, supports, adjacency):
    if start in supports:
        return 0

    seen = {start}
    frontier = [(start, 0)]
    while frontier:
        current, depth = frontier.pop(0)
        for neighbor in sorted(adjacency[current]):
            if neighbor in seen:
                continue
            if neighbor in supports:
                return depth + 1
            seen.add(neighbor)
            frontier.append((neighbor, depth + 1))
    return None


def benchmark_graph_diagnostics(graph, bounds, tolerance=1e-6):
    descriptors = extract_graph_descriptors(graph, tolerance=tolerance)
    bounds_check = bounds_contains_graph(graph, bounds, eps=tolerance)
    support_metrics = support_distance_metrics(graph, tolerance=tolerance)
    suspicious_joints = _two_member_non_collinear_joints(graph, tolerance=tolerance)
    return {
        "inside_bounds": bounds_check["inside_bounds"],
        "outside_node_ids": bounds_check["outside_node_ids"],
        "outside_edge_ids": bounds_check["outside_edge_ids"],
        "duplicate_node_count": descriptors["duplicate_node_count"],
        "duplicate_edge_count": descriptors["duplicate_edge_count"],
        "crossing_edge_count": descriptors["crossing_edge_count"],
        "overlapping_edge_count": descriptors["overlapping_edge_count"],
        "two_member_non_collinear_joint_count": len(suspicious_joints),
        "two_member_non_collinear_joints": suspicious_joints,
        "nearest_support_distance": support_metrics["nearest_support_distance"],
        "nearest_support_hops": support_metrics["nearest_support_hops"],
        "support_reachable_path_count": support_metrics["support_reachable_path_count"],
        "active_temp_force_node_ids": support_metrics["active_temp_force_node_ids"],
        "total_temp_force_magnitude": total_temp_force_magnitude(graph, eps=tolerance),
        "graph_descriptors": descriptors,
    }


def export_ml_ready(graph, evaluation_result, tolerance=1e-6):
    descriptors = extract_graph_descriptors(graph, tolerance=tolerance)
    degree_map = _node_degree_map(graph)
    node_keys = _node_keys(graph)
    node_index = {key: index for index, key in enumerate(node_keys)}
    load_nodes = {str(load.get("node")) for load in graph.get_loads()}

    node_features = []
    for key in node_keys:
        xyz = _node_xyz(graph, key)
        node_features.append(
            [
                xyz[0],
                xyz[1],
                1 if any(_fixed(graph, key)) else 0,
                1 if key in load_nodes else 0,
                degree_map[key],
                1 if _vector_magnitude(_temp_force(graph, key)) > tolerance else 0,
            ]
        )

    edge_index = []
    edge_features = []
    for u, v in _edge_pairs(graph):
        xyz_u = _node_xyz(graph, u)
        xyz_v = _node_xyz(graph, v)
        dx = xyz_v[0] - xyz_u[0]
        dy = xyz_v[1] - xyz_u[1]
        dz = xyz_v[2] - xyz_u[2]
        length = sqrt(dx * dx + dy * dy + dz * dz)
        force_mag = max(_vector_magnitude(_temp_force(graph, u)), _vector_magnitude(_temp_force(graph, v)))
        edge_index.append([node_index[u], node_index[v]])
        edge_features.append(
            [
                length,
                dx,
                dy,
                1,
                1 if force_mag > tolerance else 0,
                force_mag,
            ]
        )

    residual_magnitude = (
        evaluation_result.get("channels", {})
        .get("global_equilibrium_v1", {})
        .get("metrics", {})
        .get("residual_magnitude", 0.0)
    )

    global_features = [
        residual_magnitude,
        len(node_keys),
        len(_edge_pairs(graph)),
        count_temp_force_nodes(graph, eps=tolerance),
        descriptors["crossing_edge_count"],
        descriptors["overlapping_edge_count"],
        descriptors["connected_component_count"],
    ]

    return {
        "node_ids": node_keys,
        "node_feature_names": [
            "x",
            "y",
            "is_support",
            "is_load",
            "degree",
            "incident_temp_force_count",
        ],
        "node_features": node_features,
        "edge_index": edge_index,
        "edge_feature_names": [
            "length",
            "dx",
            "dy",
            "is_accepted_member",
            "is_temp_force_related",
            "provisional_force_mag_if_available",
        ],
        "edge_features": edge_features,
        "global_feature_names": [
            "residual_magnitude",
            "node_count",
            "edge_count",
            "temp_force_count",
            "crossing_edge_count",
            "overlapping_edge_count",
            "connected_components_count",
        ],
        "global_features": global_features,
    }


def candidate_geometry_digest(graph, candidate):
    rule_name = candidate.rule_name
    payload = dict(candidate.payload)
    segments = []
    points = []

    if rule_name == "extend_node_rule":
        node = str(payload["node"])
        start = _node_xyz(graph, node)
        direction = _normalize(_temp_force(graph, node))
        length = float(payload.get("length", 0.0))
        if direction is not None:
            end = [
                start[0] + direction[0] * length,
                start[1] + direction[1] * length,
                start[2] + direction[2] * length,
            ]
            points.append({"xyz": end})
            segments.append({"start": start, "end": end})

    elif rule_name == "split_node_rule":
        node = str(payload["node"])
        start = _node_xyz(graph, node)
        direction = _normalize(_temp_force(graph, node))
        theta = float(payload.get("theta", 0.0))
        if direction is not None:
            length = 1.0
            dir_a = _rotate_z(direction, theta)
            dir_b = _rotate_z(direction, -theta)
            end_a = [start[0] + length * dir_a[0], start[1] + length * dir_a[1], start[2] + length * dir_a[2]]
            end_b = [start[0] + length * dir_b[0], start[1] + length * dir_b[1], start[2] + length * dir_b[2]]
            points.extend([{"xyz": end_a}, {"xyz": end_b}])
            segments.extend([{"start": start, "end": end_a}, {"start": start, "end": end_b}])

    elif rule_name == "triangle_closure_rule":
        u = str(payload["u"])
        v = str(payload["v"])
        segments.append({"start": _node_xyz(graph, u), "end": _node_xyz(graph, v)})

    elif rule_name == "loa_intersection_rule":
        node_a = str(payload["node_a"])
        node_b = str(payload["node_b"])
        intersection = [float(v) for v in payload.get("intersection", [0.0, 0.0, 0.0])]
        points.append({"xyz": intersection})
        segments.append({"start": _node_xyz(graph, node_a), "end": intersection})
        segments.append({"start": _node_xyz(graph, node_b), "end": intersection})

    return {
        "rule_name": rule_name,
        "payload": payload,
        "segments": segments,
        "points": points,
    }


def explored_geometry_digest(trace):
    rule_counts = {}
    total_segments = 0
    total_points = 0

    for item in trace:
        for geometry in item.get("candidate_geometry", []):
            rule_name = geometry["rule_name"]
            rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1
            total_segments += len(geometry.get("segments", []))
            total_points += len(geometry.get("points", []))

    return {
        "candidate_geometry_count": sum(rule_counts.values()),
        "explored_segments_count": total_segments,
        "explored_points_count": total_points,
        "rule_candidate_counts": rule_counts,
    }
