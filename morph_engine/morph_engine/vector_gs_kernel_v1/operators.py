from .geometry import add
from .geometry import angle_xy
from .geometry import bidirected_ray_intersection
from .geometry import cross_z
from .geometry import directed_ray_intersection
from .geometry import distance
from .geometry import dot
from .geometry import inside_rect
from .geometry import magnitude
from .geometry import project_point_to_segment
from .geometry import rotate_z
from .geometry import scale
from .geometry import sub
from .geometry import unit
from .model import Force
from .model import ForceDirection
from .model import ForceKind
from .model import Node
from .model import NodeType


CONNECTION_TOLERANCE = 1e-9


def _segments_overlap(p1, p2, q1, q2, tolerance):
    if abs(cross_z(sub(p2, p1), sub(q1, p1))) > tolerance:
        return False
    if abs(cross_z(sub(p2, p1), sub(q2, p1))) > tolerance:
        return False
    axis = 0 if abs(p2[0] - p1[0]) >= abs(p2[1] - p1[1]) else 1
    left = max(min(p1[axis], p2[axis]), min(q1[axis], q2[axis]))
    right = min(max(p1[axis], p2[axis]), max(q1[axis], q2[axis]))
    return right - left > tolerance


def _segments_cross(p1, p2, q1, q2, tolerance):
    """Return True only for a proper interior intersection."""
    def orientation(a, b, c):
        return cross_z(sub(b, a), sub(c, a))

    o1 = orientation(p1, p2, q1)
    o2 = orientation(p1, p2, q2)
    o3 = orientation(q1, q2, p1)
    o4 = orientation(q1, q2, p2)
    if any(abs(value) <= tolerance for value in (o1, o2, o3, o4)):
        return False
    return (o1 > 0.0) != (o2 > 0.0) and (o3 > 0.0) != (o4 > 0.0)


def segment_is_admissible(assembly, start_node_id, end_node_id, start, end, tolerance=CONNECTION_TOLERANCE):
    if start_node_id == end_node_id or distance(start, end) <= tolerance:
        return False
    if assembly.member_between(start_node_id, end_node_id) is not None:
        return False
    for member in assembly.members:
        member_start = assembly.node(member.start_node).coordinate
        member_end = assembly.node(member.end_node).coordinate
        if _segments_overlap(start, end, member_start, member_end, tolerance):
            return False
        if _segments_cross(start, end, member_start, member_end, tolerance):
            return False
    return True


def make_force(point, vector, kind, direction=ForceDirection.COMPRESSION, **metadata):
    return Force(point=list(point), vector=[float(vector[0]), float(vector[1]), float(vector[2])], kind=kind, direction=direction, metadata=metadata)


def translate_force(force, coordinate):
    return Force(
        point=list(coordinate),
        vector=list(force.vector),
        kind=force.kind,
        direction=force.direction,
        related_member=force.related_member,
        metadata=dict(force.metadata),
    )


def reverse_force(force):
    return Force(
        point=list(force.point),
        vector=scale(force.vector, -1.0),
        kind=force.kind,
        direction=force.direction * -1,
        related_member=force.related_member,
        metadata=dict(force.metadata),
    )


def get_temp_force(node):
    return node.get_temp_force()


def flip_temp_force_dir(node):
    temp = get_temp_force(node)
    if temp is None:
        return node
    node.remove_temp_forces()
    node.add_force(reverse_force(temp))
    rearrange_forces(node)
    return node


def get_line_of_action(node):
    temp = get_temp_force(node)
    if temp is None:
        return None
    direction = unit(temp.vector)
    if direction is None:
        return None
    return {"point": list(node.coordinate), "direction": direction}


def transfer_member_force(force, coordinate):
    return Force(
        point=list(coordinate),
        vector=scale(force.vector, -1.0),
        kind=ForceKind.MEMBER,
        direction=force.direction,
        related_member=force.related_member,
        metadata=dict(force.metadata),
    )


def rearrange_forces(node):
    node.forces = sorted(node.forces, key=lambda force: -angle_xy(force.vector))
    return node


def equilibrate_node(node, tolerance=1e-12):
    node = rearrange_forces(node)
    total = [0.0, 0.0, 0.0]
    for force in node.forces:
        total = add(total, force.vector)
    if magnitude(total) <= tolerance:
        node.active = False
        return node
    temp = make_force(
        node.coordinate,
        scale(total, -1.0),
        ForceKind.TEMPORARY,
        direction=ForceDirection.COMPRESSION,
        semantic_origin="equilibrate_node",
    )
    node.remove_temp_forces()
    node.add_force(temp)
    node.active = True
    return rearrange_forces(node)


def temp_node_equilibrium(node):
    node.forces = [
        make_force(node.coordinate, [0.0, -1.0, 0.0], ForceKind.TEMPORARY),
        make_force(node.coordinate, rotate_z([0.0, -1.0, 0.0], 2.0943951023931953), ForceKind.TEMPORARY),
        make_force(node.coordinate, rotate_z([0.0, -1.0, 0.0], 4.1887902047863905), ForceKind.TEMPORARY),
    ]
    node.active = True
    return rearrange_forces(node)


def decompose_force_along_directions(force_vector, direction_a, direction_b, tolerance=1e-12):
    det = direction_a[0] * direction_b[1] - direction_a[1] * direction_b[0]
    if abs(det) <= tolerance:
        return None
    fx = float(force_vector[0])
    fy = float(force_vector[1])
    scale_a = (fx * direction_b[1] - fy * direction_b[0]) / det
    scale_b = (fy * direction_a[0] - fx * direction_a[1]) / det
    return {
        "vector_a": [scale_a * direction_a[0], scale_a * direction_a[1], scale_a * direction_a[2]],
        "vector_b": [scale_b * direction_b[0], scale_b * direction_b[1], scale_b * direction_b[2]],
        "scale_a": scale_a,
        "scale_b": scale_b,
    }


def active_nodes(assembly):
    return [node for node in assembly.nodes if node.active and get_temp_force(node) is not None]


def closest_active_nodes(node, assembly, count=1):
    others = [other for other in active_nodes(assembly) if other.node_id != node.node_id]
    ordered = sorted(others, key=lambda other: (distance(node.coordinate, other.coordinate), other.node_id))
    return ordered[:count]


def closest_projection(node, assembly, count=6, bidirectional=False):
    loa = get_line_of_action(node)
    if loa is None:
        return None
    intersect = bidirected_ray_intersection if bidirectional else directed_ray_intersection
    best = None
    for other in closest_active_nodes(node, assembly, count=count):
        other_loa = get_line_of_action(other)
        if other_loa is None:
            continue
        point = intersect(loa["point"], loa["direction"], other_loa["point"], other_loa["direction"])
        if point is None:
            continue
        dist = distance(node.coordinate, point)
        if best is None or dist < best["distance"]:
            best = {"other": other, "point": point, "distance": dist}
    return best


def closest_link(node, assembly):
    return closest_projection(node, assembly, count=6, bidirectional=False)


def connection_is_non_degenerate(node_a, node_b, assembly, intersection, tolerance=CONNECTION_TOLERANCE):
    if node_a.node_id == node_b.node_id:
        return False
    if assembly.member_between(node_a.node_id, node_b.node_id) is not None:
        return False
    if distance(node_a.coordinate, intersection) <= tolerance:
        return False
    if distance(node_b.coordinate, intersection) <= tolerance:
        return False
    if assembly.node_exists_at(intersection, tolerance=tolerance):
        return False
    candidate_id = "__connection_candidate__"
    if not segment_is_admissible(assembly, node_a.node_id, candidate_id, node_a.coordinate, intersection, tolerance):
        return False
    if not segment_is_admissible(assembly, node_b.node_id, candidate_id, node_b.coordinate, intersection, tolerance):
        return False
    return True


def closure_ray_candidate(node_a, node_b, assembly, source_ray_sign, target_ray_sign, tolerance=CONNECTION_TOLERANCE):
    record = {
        "source_node": node_a.node_id,
        "target_node": node_b.node_id,
        "source_ray_sign": int(source_ray_sign),
        "target_ray_sign": int(target_ray_sign),
        "intersection": None,
        "source_ray_parameter": None,
        "target_ray_parameter": None,
        "distance_measure": None,
        "rejection_reason": None,
    }
    loa_a = get_line_of_action(node_a)
    loa_b = get_line_of_action(node_b)
    if loa_a is None or loa_b is None:
        record["rejection_reason"] = "missing_line_of_action"
        return record
    direction_a = scale(loa_a["direction"], source_ray_sign)
    direction_b = scale(loa_b["direction"], target_ray_sign)
    determinant = cross_z(direction_a, direction_b)
    if abs(determinant) <= tolerance:
        record["rejection_reason"] = "parallel_rays"
        return record
    delta = sub(node_b.coordinate, node_a.coordinate)
    source_parameter = cross_z(delta, direction_b) / determinant
    target_parameter = cross_z(delta, direction_a) / determinant
    record["source_ray_parameter"] = float(source_parameter)
    record["target_ray_parameter"] = float(target_parameter)
    if source_parameter < -tolerance or target_parameter < -tolerance:
        record["rejection_reason"] = "negative_ray_parameter"
        return record
    intersection = add(node_a.coordinate, scale(direction_a, source_parameter))
    record["intersection"] = list(intersection)
    record["distance_measure"] = float(distance(node_a.coordinate, intersection))
    if not boundary_ok(intersection, assembly):
        record["rejection_reason"] = "intersection_outside_bounds"
        return record
    if not connection_is_non_degenerate(node_a, node_b, assembly, intersection, tolerance):
        record["rejection_reason"] = "inadmissible_connection"
        return record
    return record


def connect_two_forces(node_a, node_b, assembly, intersection, source_ray_sign=1, target_ray_sign=1):
    temp_a = get_temp_force(node_a)
    temp_b = get_temp_force(node_b)
    if temp_a is None or temp_b is None or not connection_is_non_degenerate(node_a, node_b, assembly, intersection):
        return False
    connector_a = unit(sub(intersection, node_a.coordinate))
    connector_b = unit(sub(intersection, node_b.coordinate))
    temp_direction_a = unit(temp_a.vector)
    temp_direction_b = unit(temp_b.vector)
    if connector_a is None or connector_b is None or temp_direction_a is None or temp_direction_b is None:
        return False
    direction_a = ForceDirection.TENSION if dot(temp_direction_a, connector_a) >= 0.0 else ForceDirection.COMPRESSION
    direction_b = ForceDirection.TENSION if dot(temp_direction_b, connector_b) >= 0.0 else ForceDirection.COMPRESSION
    force_a = make_force(
        node_a.coordinate,
        temp_a.vector,
        ForceKind.MEMBER,
        direction=direction_a,
        semantic_origin="connect_two_forces",
        ray_sign=int(source_ray_sign),
    )
    force_b = make_force(
        node_b.coordinate,
        temp_b.vector,
        ForceKind.MEMBER,
        direction=direction_b,
        semantic_origin="connect_two_forces",
        ray_sign=int(target_ray_sign),
    )
    node_a.remove_temp_forces()
    node_b.remove_temp_forces()
    node_a.add_force(force_a)
    node_b.add_force(force_b)
    node_a.active = False
    node_b.active = False
    rearrange_forces(node_a)
    rearrange_forces(node_b)

    new_node = Node(node_id=assembly.next_node_id(), coordinate=list(intersection), type=NodeType.CORNER, forces=[], active=True)
    new_node.add_force(transfer_member_force(force_a, intersection))
    new_node.add_force(transfer_member_force(force_b, intersection))
    equilibrate_node(new_node)
    assembly.add_node(new_node)
    assembly.add_member(assembly_member_between(assembly, node_a.node_id, new_node.node_id, force_a))
    assembly.add_member(assembly_member_between(assembly, node_b.node_id, new_node.node_id, force_b))
    return True


def can_resolve_two_forces(assembly, tolerance=CONNECTION_TOLERANCE):
    nodes = active_nodes(assembly)
    if len(nodes) != 2:
        return False
    node_a, node_b = nodes
    if node_a.node_id == node_b.node_id or assembly.member_between(node_a.node_id, node_b.node_id) is not None:
        return False
    temp_a = get_temp_force(node_a)
    temp_b = get_temp_force(node_b)
    if temp_a is None or temp_b is None:
        return False
    connector = sub(node_b.coordinate, node_a.coordinate)
    connector_dir = unit(connector)
    temp_a_dir = unit(temp_a.vector)
    temp_b_dir = unit(temp_b.vector)
    if connector_dir is None or temp_a_dir is None or temp_b_dir is None:
        return False
    if magnitude(add(temp_a.vector, temp_b.vector)) > tolerance:
        return False
    if abs(abs(dot(temp_a_dir, connector_dir)) - 1.0) > tolerance:
        return False
    if not segment_is_admissible(assembly, node_a.node_id, node_b.node_id, node_a.coordinate, node_b.coordinate, tolerance):
        return False
    return True


def resolve_two_forces(assembly):
    if not can_resolve_two_forces(assembly):
        return False
    node_a, node_b = active_nodes(assembly)
    temp_a = get_temp_force(node_a)
    temp_b = get_temp_force(node_b)
    connector_dir = unit(sub(node_b.coordinate, node_a.coordinate))
    temp_dir = unit(temp_a.vector)
    direction = ForceDirection.TENSION if dot(temp_dir, connector_dir) >= 0.0 else ForceDirection.COMPRESSION
    force_a = make_force(node_a.coordinate, temp_a.vector, ForceKind.MEMBER, direction=direction, semantic_origin="resolve_two_forces")
    force_b = make_force(node_b.coordinate, temp_b.vector, ForceKind.MEMBER, direction=direction, semantic_origin="resolve_two_forces")
    node_a.remove_temp_forces()
    node_b.remove_temp_forces()
    node_a.add_force(force_a)
    node_b.add_force(force_b)
    node_a.active = False
    node_b.active = False
    rearrange_forces(node_a)
    rearrange_forces(node_b)
    assembly.add_member(assembly_member_between(assembly, node_a.node_id, node_b.node_id, force_a))
    return True


def three_force_closure_hub(assembly, tolerance=CONNECTION_TOLERANCE):
    nodes = active_nodes(assembly)
    if len(nodes) != 3:
        return None
    temps = [get_temp_force(node) for node in nodes]
    if any(temp is None for temp in temps):
        return None
    if magnitude(add(add(temps[0].vector, temps[1].vector), temps[2].vector)) > tolerance:
        return None
    for hub in nodes:
        others = [node for node in nodes if node.node_id != hub.node_id]
        admissible = True
        for other in others:
            member_direction = unit(sub(hub.coordinate, other.coordinate))
            temp_direction = unit(get_temp_force(other).vector)
            if member_direction is None or temp_direction is None:
                admissible = False
                break
            if abs(abs(dot(member_direction, temp_direction)) - 1.0) > tolerance:
                admissible = False
                break
            if not segment_is_admissible(
                assembly,
                other.node_id,
                hub.node_id,
                other.coordinate,
                hub.coordinate,
                tolerance,
            ):
                admissible = False
                break
        if admissible:
            return hub
    return None


def resolve_three_forces_at_existing_node(assembly):
    hub = three_force_closure_hub(assembly)
    if hub is None:
        return False
    nodes = active_nodes(assembly)
    others = [node for node in nodes if node.node_id != hub.node_id]
    hub.remove_temp_forces()
    for other in others:
        temp = get_temp_force(other)
        connector_direction = unit(sub(hub.coordinate, other.coordinate))
        temp_direction = unit(temp.vector)
        direction = ForceDirection.TENSION if dot(temp_direction, connector_direction) >= 0.0 else ForceDirection.COMPRESSION
        member_force = make_force(
            other.coordinate,
            temp.vector,
            ForceKind.MEMBER,
            direction=direction,
            semantic_origin="resolve_three_forces_at_existing_node",
        )
        other.remove_temp_forces()
        other.add_force(member_force)
        other.active = False
        hub.add_force(transfer_member_force(member_force, hub.coordinate))
        assembly.add_member(assembly_member_between(assembly, other.node_id, hub.node_id, member_force))
        rearrange_forces(other)
    hub.active = False
    rearrange_forces(hub)
    return True


def support_projection_target(node, assembly):
    supports = assembly.support_nodes()
    if len(supports) < 2:
        return None
    segment_a = supports[0].coordinate
    segment_b = supports[-1].coordinate
    projection = project_point_to_segment(node.coordinate, segment_a, segment_b)
    return projection


def support_link_target(node, assembly, alignment_threshold=0.85):
    loa = get_line_of_action(node)
    if loa is None:
        return None
    best = None
    for support in assembly.support_nodes():
        direction = unit(sub(support.coordinate, node.coordinate))
        if direction is None:
            continue
        alignment = dot(direction, loa["direction"])
        if alignment < alignment_threshold:
            continue
        dist = distance(node.coordinate, support.coordinate)
        if best is None or alignment > best["alignment"] or (alignment == best["alignment"] and dist < best["distance"]):
            best = {"support": support, "alignment": alignment, "distance": dist}
    return best


def assembly_member_between(assembly, node_a, node_b, force):
    existing = assembly.member_between(node_a, node_b)
    if existing is not None:
        return existing
    from .model import Member

    member_id = assembly.next_member_id()
    force.related_member = member_id

    # Attach the generated member identity to the equal-and-opposite endpoint
    # force records. This is evidence metadata only; no rule or policy reads it.
    expected_vectors = {
        str(node_a): list(force.vector),
        str(node_b): scale(force.vector, -1.0),
    }
    for node_id, expected in expected_vectors.items():
        for endpoint_force in reversed(assembly.node(node_id).member_forces()):
            if endpoint_force.related_member is not None:
                continue
            delta = sub(endpoint_force.vector, expected)
            if magnitude(delta) <= CONNECTION_TOLERANCE:
                endpoint_force.related_member = member_id
                break

    return Member(
        member_id=member_id,
        start_node=str(node_a),
        end_node=str(node_b),
        force=Force(
            point=list(force.point),
            vector=list(force.vector),
            kind=force.kind,
            direction=force.direction,
            related_member=member_id,
            metadata=dict(force.metadata),
        ),
        metadata=dict(force.metadata),
    )


def boundary_ok(point, assembly):
    return inside_rect(point, assembly.boundary)


def _has_load_to_support_path(assembly):
    """Return structural load-path admissibility without evaluator scoring."""
    support_ids = {node.node_id for node in assembly.nodes if node.type == NodeType.SUPPORT}
    load_ids = [node.node_id for node in assembly.nodes if node.type == NodeType.LOAD]
    if not support_ids or not load_ids:
        return False

    adjacency = {node.node_id: set() for node in assembly.nodes}
    for member in assembly.members:
        adjacency.setdefault(member.start_node, set()).add(member.end_node)
        adjacency.setdefault(member.end_node, set()).add(member.start_node)

    for load_id in load_ids:
        queue = [load_id]
        seen = {load_id}
        while queue:
            current = queue.pop(0)
            if current in support_ids:
                return True
            for neighbor in sorted(adjacency.get(current, ())):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
    return False


def _assembly_geometry_is_admissible(assembly, tolerance):
    for node in assembly.nodes:
        if not inside_rect(node.coordinate, assembly.boundary):
            return False

    for index, node in enumerate(assembly.nodes):
        if any(distance(node.coordinate, other.coordinate) <= tolerance for other in assembly.nodes[index + 1 :]):
            return False

    member_pairs = set()
    for member in assembly.members:
        pair = tuple(sorted((member.start_node, member.end_node)))
        if pair in member_pairs:
            return False
        member_pairs.add(pair)
        start = assembly.node(member.start_node).coordinate
        end = assembly.node(member.end_node).coordinate
        if distance(start, end) <= tolerance:
            return False

    for index, member_a in enumerate(assembly.members):
        p1 = assembly.node(member_a.start_node).coordinate
        p2 = assembly.node(member_a.end_node).coordinate
        endpoints_a = {member_a.start_node, member_a.end_node}
        for member_b in assembly.members[index + 1 :]:
            if endpoints_a & {member_b.start_node, member_b.end_node}:
                continue
            q1 = assembly.node(member_b.start_node).coordinate
            q2 = assembly.node(member_b.end_node).coordinate
            if _segments_overlap(p1, p2, q1, q2, tolerance):
                return False
            if _segments_cross(p1, p2, q1, q2, tolerance):
                return False
    return True


def structural_completion_reason(assembly, tolerance=CONNECTION_TOLERANCE):
    """Return method-level admissibility only; never consume evaluator metrics.

    Verification is intentionally limited to structural semantics that must
    hold for every policy: resolved fronts, nodal equilibrium, axial
    action-reaction, a load-to-support path, and backend geometric
    admissibility. Benchmark scores and design objectives remain observational.
    """
    unresolved = [
        node.node_id
        for node in assembly.nodes
        if node.active or get_temp_force(node) is not None
    ]
    if unresolved:
        return "unresolved_force_fronts"

    for node in assembly.nodes:
        total = [0.0, 0.0, 0.0]
        for force in node.forces:
            if force.kind != ForceKind.TEMPORARY:
                total = add(total, force.vector)
        if magnitude(total) > tolerance:
            return "no_valid_closure"

    for member in assembly.members:
        start = assembly.node(member.start_node)
        end = assembly.node(member.end_node)
        axis = unit(sub(end.coordinate, start.coordinate))
        if axis is None or member.force is None:
            return "no_valid_closure"
        force_direction = unit(member.force.vector)
        if force_direction is None or abs(abs(dot(axis, force_direction)) - 1.0) > tolerance:
            return "no_valid_closure"
        start_match = any(
            force.kind == ForceKind.MEMBER and magnitude(sub(force.vector, member.force.vector)) <= tolerance
            for force in start.forces
        )
        end_match = any(
            force.kind == ForceKind.MEMBER and magnitude(add(force.vector, member.force.vector)) <= tolerance
            for force in end.forces
        )
        if not start_match or not end_match:
            return "no_valid_closure"

    if not _has_load_to_support_path(assembly):
        return "no_valid_closure"
    if not _assembly_geometry_is_admissible(assembly, tolerance):
        return "geometrically_invalid"
    return None
