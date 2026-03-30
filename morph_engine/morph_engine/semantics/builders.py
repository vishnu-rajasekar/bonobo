from .assembly_view import StructuralAssemblyView
from .force import StructuralForce
from .member import build_structural_member_view as _build_member_view
from .node import StructuralNodeView


def _node_xyz(graph, node_key):
    xyz = graph.network.node_attribute(node_key, "xyz") or [0.0, 0.0, 0.0]
    return [float(xyz[0]), float(xyz[1]), float(xyz[2])]


def _ordered_edge_key(u, v):
    su = str(u)
    sv = str(v)
    return (su, sv) if su <= sv else (sv, su)


def _support_node_ids(graph):
    support_ids = []
    for node_key in graph.network.nodes():
        fixed = graph.network.node_attribute(node_key, "fixed") or [0, 0, 0]
        if any(float(value) != 0.0 for value in fixed):
            support_ids.append(str(node_key))
    return sorted(support_ids)


def _load_vectors(graph):
    by_node = {}
    for load in graph.get_loads():
        node_id = str(load.get("node"))
        vector = [float(value) for value in load.get("vector", [0.0, 0.0, 0.0])]
        by_node.setdefault(node_id, []).append(vector)
    return by_node


def _member_force_at_node(member_view, node_id):
    record = member_view.force_record or {}
    vector = record.get("vector")
    if vector is None:
        return None

    source_node = record.get("source_node")
    if source_node is not None:
        if str(source_node) == str(node_id):
            oriented = [float(vector[0]), float(vector[1]), float(vector[2])]
        else:
            oriented = [-float(vector[0]), -float(vector[1]), -float(vector[2])]
    elif str(node_id) == member_view.node_u:
        oriented = [float(vector[0]), float(vector[1]), float(vector[2])]
    else:
        oriented = [-float(vector[0]), -float(vector[1]), -float(vector[2])]

    return StructuralForce(
        force_id="member:{0}:{1}@{2}".format(member_view.edge_key[0], member_view.edge_key[1], node_id),
        kind="member",
        vector=oriented,
        direction_kind=record.get("direction_kind"),
        source_node=str(node_id),
        target_node=record.get("target_node"),
        related_member=member_view.edge_key,
        line_of_action_point=_node_xyz_from_member(member_view, node_id),
        status=str(record.get("status") or "explicit"),
        provenance=str(record.get("provenance") or "graph_derived"),
        metadata={
            "family": member_view.family,
            "record": dict(record),
        },
    )


def _node_xyz_from_member(member_view, node_id):
    if str(node_id) == member_view.node_u:
        return list(member_view.u_xyz)
    return list(member_view.v_xyz)


def build_structural_member_view(graph, edge_id):
    return _build_member_view(graph, edge_id)


def build_structural_node_view(graph, node_id):
    node_id = str(node_id)
    xyz = _node_xyz(graph, node_id)
    support_ids = set(_support_node_ids(graph))
    load_vectors = _load_vectors(graph)
    load_nodes = set(load_vectors.keys())

    incident_members = []
    local_forces = []

    for index, force_record in enumerate(graph.get_node_forces(node_id)):
        local_forces.append(
            StructuralForce(
                force_id="node_force:{0}:{1}".format(node_id, index),
                kind=str(force_record.get("kind") or "temporary"),
                vector=[float(value) for value in force_record.get("vector", [0.0, 0.0, 0.0])],
                direction_kind=force_record.get("direction_kind"),
                source_node=node_id,
                target_node=None if force_record.get("target_node") is None else str(force_record.get("target_node")),
                related_member=None
                if force_record.get("related_member") is None
                else tuple([str(value) for value in force_record.get("related_member")]),
                line_of_action_point=xyz,
                status=str(force_record.get("status") or "explicit"),
                provenance=str(force_record.get("provenance") or "graph_explicit"),
                metadata=dict(force_record.get("metadata") or {}),
            )
        )

    for neighbor in graph.network.neighbors(node_id):
        key = _ordered_edge_key(node_id, neighbor)
        incident_members.append(key)
        member_view = _build_member_view(graph, key)
        member_force = _member_force_at_node(member_view, node_id)
        if member_force is not None:
            local_forces.append(member_force)

    for index, vector in enumerate(load_vectors.get(node_id, [])):
        local_forces.append(
            StructuralForce(
                force_id="load:{0}:{1}".format(node_id, index),
                kind="load",
                vector=vector,
                source_node=node_id,
                line_of_action_point=xyz,
                status="explicit",
                provenance="graph_loadcase",
                metadata={},
            )
        )

    temp_force = [float(value) for value in (graph.get_temp_force(node_id) or [0.0, 0.0, 0.0])]
    if any(abs(value) > 1e-12 for value in temp_force):
        local_forces.append(
            StructuralForce(
                force_id="temp:{0}".format(node_id),
                kind="temporary",
                vector=temp_force,
                source_node=node_id,
                line_of_action_point=xyz,
                status="explicit",
                provenance="graph_temp_force",
                metadata={},
            )
        )

    node_kind = "internal"
    if node_id in support_ids:
        node_kind = "support"
    elif node_id in load_nodes:
        node_kind = "load"

    return StructuralNodeView(
        node_id=node_id,
        xyz=xyz,
        node_kind=node_kind,
        degree=int(graph.network.degree(node_id)),
        incident_member_ids=sorted(incident_members),
        local_forces=local_forces,
        support=node_id in support_ids,
        load=node_id in load_nodes,
    )


def build_structural_assembly_view(graph):
    members = {}
    for u, v in graph.network.edges():
        key = _ordered_edge_key(u, v)
        members[key] = _build_member_view(graph, key)

    nodes = {}
    for node_id in graph.network.nodes():
        nodes[str(node_id)] = build_structural_node_view(graph, node_id)

    return StructuralAssemblyView(
        nodes=nodes,
        members=members,
        support_node_ids=_support_node_ids(graph),
        load_node_ids=sorted(_load_vectors(graph).keys()),
    )
