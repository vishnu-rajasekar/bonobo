from collections import Counter

from .geometry import distance
from .geometry import inside_rect
from .geometry import magnitude
from .geometry import unit
from .model import ForceKind
from .model import NodeType


DEFAULT_TOLERANCE = 1e-9


def _adjacency(assembly):
    adjacency = {node.node_id: set() for node in assembly.nodes}
    for member in assembly.members:
        adjacency.setdefault(member.start_node, set()).add(member.end_node)
        adjacency.setdefault(member.end_node, set()).add(member.start_node)
    return adjacency


def _support_connectivity(assembly):
    support_ids = {node.node_id for node in assembly.nodes if node.type == NodeType.SUPPORT}
    load_ids = [node.node_id for node in assembly.nodes if node.type == NodeType.LOAD]
    if not support_ids or not load_ids:
        return {"support_connected": False, "support_path_count": 0}

    adjacency = _adjacency(assembly)
    path_count = 0
    for load_id in load_ids:
        queue = [load_id]
        seen = {load_id}
        connected = False
        while queue:
            current = queue.pop(0)
            if current in support_ids:
                connected = True
                break
            for neighbor in sorted(adjacency.get(current, ())):
                if neighbor in seen:
                    continue
                seen.add(neighbor)
                queue.append(neighbor)
        if connected:
            path_count += 1
    return {
        "support_connected": path_count > 0,
        "support_path_count": path_count,
    }


def _member_lengths(assembly):
    node_by_id = {node.node_id: node for node in assembly.nodes}
    lengths = []
    for member in assembly.members:
        start = node_by_id[member.start_node].coordinate
        end = node_by_id[member.end_node].coordinate
        lengths.append(distance(start, end))
    return lengths


def _valence_stats(assembly):
    adjacency = _adjacency(assembly)
    valences = [len(adjacency.get(node.node_id, ())) for node in assembly.nodes]
    if not valences:
        return {"min": 0, "max": 0, "mean": 0.0}
    return {
        "min": min(valences),
        "max": max(valences),
        "mean": sum(valences) / float(len(valences)),
    }


def _vector_sum(vectors):
    total = [0.0, 0.0, 0.0]
    for vector in vectors:
        total[0] += float(vector[0])
        total[1] += float(vector[1])
        total[2] += float(vector[2])
    return total


def _scale(vector, factor):
    return [float(vector[0]) * factor, float(vector[1]) * factor, float(vector[2]) * factor]


def _dot_2d(a, b):
    return float(a[0]) * float(b[0]) + float(a[1]) * float(b[1])


def _cross_2d(a, b):
    return float(a[0]) * float(b[1]) - float(a[1]) * float(b[0])


def _solve_reaction_coefficients_2d(directions, target, tolerance):
    if not directions:
        return []

    if len(directions) == 1:
        denom = _dot_2d(directions[0], directions[0])
        if denom <= tolerance:
            return [0.0]
        return [_dot_2d(target, directions[0]) / denom]

    first = directions[0]
    if all(abs(_cross_2d(first, direction)) <= tolerance for direction in directions[1:]):
        denom = sum(_dot_2d(direction, first) for direction in directions)
        if abs(denom) <= tolerance:
            return [0.0 for _ in directions]
        shared = _dot_2d(target, first) / denom
        return [shared for _ in directions]

    s_xx = sum(float(direction[0]) * float(direction[0]) for direction in directions)
    s_xy = sum(float(direction[0]) * float(direction[1]) for direction in directions)
    s_yy = sum(float(direction[1]) * float(direction[1]) for direction in directions)
    det = s_xx * s_yy - s_xy * s_xy
    if abs(det) <= tolerance:
        return [0.0 for _ in directions]

    lambda_x = (float(target[0]) * s_yy - s_xy * float(target[1])) / det
    lambda_y = (s_xx * float(target[1]) - s_xy * float(target[0])) / det
    return [float(direction[0]) * lambda_x + float(direction[1]) * lambda_y for direction in directions]


def _reaction_direction_for_node(assembly, node):
    by_node = assembly.metadata.get("reaction_directions_by_node", {})
    direction = by_node.get(node.node_id) or node.metadata.get("reaction_direction")
    if direction is None:
        return None
    if magnitude(direction) <= DEFAULT_TOLERANCE:
        return None
    return unit(direction)


def _boundary_force_polygon(assembly, tolerance=DEFAULT_TOLERANCE):
    applied_forces = []
    for node in assembly.nodes:
        for force in node.forces:
            if force.kind == ForceKind.APPLIED:
                applied_forces.append(
                    {
                        "node_id": node.node_id,
                        "point": list(force.point),
                        "vector": list(force.vector),
                    }
                )

    reaction_directions = []
    for node in assembly.support_nodes():
        direction = _reaction_direction_for_node(assembly, node)
        if direction is not None:
            reaction_directions.append(
                {
                    "node_id": node.node_id,
                    "point": list(node.coordinate),
                    "direction": direction,
                }
            )

    total_applied = _vector_sum([force["vector"] for force in applied_forces])
    target = [-total_applied[0], -total_applied[1], -total_applied[2]]
    coefficients = _solve_reaction_coefficients_2d(
        [item["direction"] for item in reaction_directions],
        target,
        tolerance,
    )

    reactions = []
    for item, coefficient in zip(reaction_directions, coefficients):
        reactions.append(
            {
                "node_id": item["node_id"],
                "point": list(item["point"]),
                "direction": list(item["direction"]),
                "magnitude": float(coefficient),
                "vector": _scale(item["direction"], float(coefficient)),
            }
        )

    total_reaction = _vector_sum([reaction["vector"] for reaction in reactions])
    residual = [
        total_applied[0] + total_reaction[0],
        total_applied[1] + total_reaction[1],
        total_applied[2] + total_reaction[2],
    ]
    residual_magnitude = magnitude(residual)

    return {
        "force_convention": assembly.metadata.get(
            "force_convention",
            "tail_to_head_vectors_head_to_tail_polygon",
        ),
        "applied_forces": applied_forces,
        "reaction_directions": reaction_directions,
        "solved_reactions": reactions,
        "total_applied_force": total_applied,
        "total_reaction_force": total_reaction,
        "polygon_residual": residual,
        "polygon_residual_magnitude": residual_magnitude,
        "externally_balanced": residual_magnitude <= tolerance,
    }


def _node_by_id(assembly):
    return {node.node_id: node for node in assembly.nodes}


def _node_coordinate_key(node, tolerance):
    return tuple(round(float(value) / tolerance) for value in node.coordinate)


def _duplicate_nodes(assembly, tolerance):
    seen = {}
    duplicates = []
    for node in assembly.nodes:
        key = _node_coordinate_key(node, tolerance)
        if key in seen:
            duplicates.append(
                {
                    "node_a": seen[key].node_id,
                    "node_b": node.node_id,
                    "distance": distance(seen[key].coordinate, node.coordinate),
                }
            )
        else:
            seen[key] = node
    return duplicates


def _duplicate_members(assembly):
    seen = {}
    duplicates = []
    for member in assembly.members:
        key = tuple(sorted([member.start_node, member.end_node]))
        seen[key] = seen.get(key, 0) + 1
    for key, count in seen.items():
        if count > 1:
            duplicates.append({"start_node": key[0], "end_node": key[1], "count": count})
    return duplicates


def _zero_length_members(assembly, tolerance):
    nodes = _node_by_id(assembly)
    zero_length = []
    for member in assembly.members:
        start = nodes[member.start_node].coordinate
        end = nodes[member.end_node].coordinate
        length = distance(start, end)
        if length <= tolerance:
            zero_length.append({"member_id": member.member_id, "length": length})
    return zero_length


def _orientation(a, b, c):
    return (float(b[0]) - float(a[0])) * (float(c[1]) - float(a[1])) - (
        float(b[1]) - float(a[1])
    ) * (float(c[0]) - float(a[0]))


def _shares_endpoint(member_a, member_b):
    return member_a.start_node in {member_b.start_node, member_b.end_node} or member_a.end_node in {
        member_b.start_node,
        member_b.end_node,
    }


def _projection_overlap(a0, a1, b0, b1, tolerance):
    left = max(min(a0, a1), min(b0, b1))
    right = min(max(a0, a1), max(b0, b1))
    return (right - left) > tolerance


def _segments_overlap(p1, p2, q1, q2, tolerance):
    o1 = _orientation(p1, p2, q1)
    o2 = _orientation(p1, p2, q2)
    if abs(o1) > tolerance or abs(o2) > tolerance:
        return False
    if abs(float(p1[0]) - float(p2[0])) >= abs(float(p1[1]) - float(p2[1])):
        return _projection_overlap(p1[0], p2[0], q1[0], q2[0], tolerance)
    return _projection_overlap(p1[1], p2[1], q1[1], q2[1], tolerance)


def _segments_cross(p1, p2, q1, q2, tolerance):
    o1 = _orientation(p1, p2, q1)
    o2 = _orientation(p1, p2, q2)
    o3 = _orientation(q1, q2, p1)
    o4 = _orientation(q1, q2, p2)
    if abs(o1) <= tolerance or abs(o2) <= tolerance or abs(o3) <= tolerance or abs(o4) <= tolerance:
        return False
    return (o1 > 0.0) != (o2 > 0.0) and (o3 > 0.0) != (o4 > 0.0)


def _member_intersections(assembly, tolerance):
    nodes = _node_by_id(assembly)
    crossing_members = []
    overlapping_members = []
    for index, member_a in enumerate(assembly.members):
        p1 = nodes[member_a.start_node].coordinate
        p2 = nodes[member_a.end_node].coordinate
        for member_b in assembly.members[index + 1 :]:
            if _shares_endpoint(member_a, member_b):
                continue
            q1 = nodes[member_b.start_node].coordinate
            q2 = nodes[member_b.end_node].coordinate
            pair = {"member_a": member_a.member_id, "member_b": member_b.member_id}
            if _segments_overlap(p1, p2, q1, q2, tolerance):
                overlapping_members.append(pair)
            elif _segments_cross(p1, p2, q1, q2, tolerance):
                crossing_members.append(pair)
    return crossing_members, overlapping_members


def compute_kernel_validity(assembly, tolerance=DEFAULT_TOLERANCE):
    duplicate_nodes = _duplicate_nodes(assembly, tolerance)
    duplicate_members = _duplicate_members(assembly)
    zero_length_members = _zero_length_members(assembly, tolerance)
    crossing_members, overlapping_members = _member_intersections(assembly, tolerance)

    out_of_bounds_nodes = [
        {"node_id": node.node_id, "coordinate": list(node.coordinate)}
        for node in assembly.nodes
        if not inside_rect(node.coordinate, assembly.boundary)
    ]

    invalid_reasons = []
    if out_of_bounds_nodes:
        invalid_reasons.append("nodes_outside_bounds")
    if duplicate_nodes:
        invalid_reasons.append("duplicate_nodes")
    if duplicate_members:
        invalid_reasons.append("duplicate_members")
    if zero_length_members:
        invalid_reasons.append("zero_length_members")
    if crossing_members:
        invalid_reasons.append("crossing_members")
    if overlapping_members:
        invalid_reasons.append("overlapping_members")

    return {
        "geometrically_valid": not invalid_reasons,
        "invalid_reasons": invalid_reasons,
        "inside_bounds": not out_of_bounds_nodes,
        "out_of_bounds_nodes": out_of_bounds_nodes,
        "out_of_bounds_node_count": len(out_of_bounds_nodes),
        "duplicate_nodes": duplicate_nodes,
        "duplicate_node_count": len(duplicate_nodes),
        "duplicate_members": duplicate_members,
        "duplicate_member_count": len(duplicate_members),
        "zero_length_members": zero_length_members,
        "zero_length_member_count": len(zero_length_members),
        "crossing_members": crossing_members,
        "crossing_member_count": len(crossing_members),
        "overlapping_members": overlapping_members,
        "overlapping_member_count": len(overlapping_members),
    }


def compute_kernel_metrics(assembly, trace=None):
    trace = trace or []
    member_lengths = _member_lengths(assembly)
    support = _support_connectivity(assembly)
    rule_counts = Counter(step.get("rule") for step in trace)
    residual_magnitude = float(assembly.residual_magnitude())
    equilibrium_reached = residual_magnitude <= DEFAULT_TOLERANCE
    validity = compute_kernel_validity(assembly)
    boundary_force_polygon = _boundary_force_polygon(assembly)
    benchmark_complete = equilibrium_reached and support["support_connected"] and validity["geometrically_valid"]

    return {
        "accepted_step_count": len(trace),
        "final_state": assembly.state,
        "final_residual_magnitude": residual_magnitude,
        "final_node_count": len(assembly.nodes),
        "final_member_count": len(assembly.members),
        "material_proxy_total_member_length": float(sum(member_lengths)),
        "member_length_stats": {
            "min": min(member_lengths) if member_lengths else 0.0,
            "max": max(member_lengths) if member_lengths else 0.0,
            "mean": (sum(member_lengths) / float(len(member_lengths))) if member_lengths else 0.0,
        },
        "valence_stats": _valence_stats(assembly),
        "support_connectivity": support,
        "equilibrium_reached": equilibrium_reached,
        "benchmark_complete": benchmark_complete,
        "boundary_force_polygon": boundary_force_polygon,
        "benchmark_validity": validity,
        "rule_counts": dict(rule_counts),
    }
