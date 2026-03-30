from dataclasses import dataclass, field
from math import sqrt
from typing import Any


def _ordered_edge_key(u, v):
    su = str(u)
    sv = str(v)
    return (su, sv) if su <= sv else (sv, su)


def _node_xyz(graph, node_key):
    xyz = graph.network.node_attribute(node_key, "xyz") or [0.0, 0.0, 0.0]
    return [float(xyz[0]), float(xyz[1]), float(xyz[2])]


def _edge_attributes(graph, u, v):
    for key in ((u, v), (v, u), _ordered_edge_key(u, v)):
        try:
            attrs = graph.network.edge_attribute(key, "attributes")
        except KeyError:
            continue
        return dict(attrs or {})
    return {}


def _set_edge_attributes(graph, u, v, attributes):
    for key in ((u, v), (v, u), _ordered_edge_key(u, v)):
        try:
            graph.network.edge_attribute(key, "attributes", dict(attributes))
            return
        except KeyError:
            continue
    raise KeyError((u, v))


def member_force_record(graph, u, v):
    attributes = _edge_attributes(graph, u, v)
    force = attributes.get("force")
    if force is not None:
        return dict(force)
    return None


def set_member_force_record(graph, u, v, force_record):
    attributes = _edge_attributes(graph, u, v)
    attributes["force"] = dict(force_record)
    _set_edge_attributes(graph, u, v, attributes)
    return dict(attributes["force"])


def create_member_force_record(vector, source_node=None, target_edge=None, metadata=None):
    magnitude = sqrt(float(vector[0]) * float(vector[0]) + float(vector[1]) * float(vector[1]) + float(vector[2]) * float(vector[2]))
    direction = None
    if magnitude > 1e-12:
        direction = [float(vector[0]) / magnitude, float(vector[1]) / magnitude, float(vector[2]) / magnitude]
    return {
        "kind": "member",
        "vector": [float(vector[0]), float(vector[1]), float(vector[2])],
        "magnitude": magnitude,
        "direction": direction,
        "source_node": None if source_node is None else str(source_node),
        "target_node": None,
        "target_edge": None if target_edge is None else [str(target_edge[0]), str(target_edge[1])],
        "direction_kind": None,
        "status": "explicit",
        "provenance": "graph_explicit",
        "metadata": dict(metadata or {}),
    }


def enrich_member_force_record(
    force_record,
    *,
    source_node=None,
    target_node=None,
    target_edge=None,
    direction_kind=None,
    status=None,
    provenance=None,
    metadata=None,
):
    enriched = dict(force_record or {})
    if source_node is not None:
        enriched["source_node"] = str(source_node)
    if target_node is not None:
        enriched["target_node"] = str(target_node)
    if target_edge is not None:
        enriched["target_edge"] = [str(target_edge[0]), str(target_edge[1])]
    if direction_kind is not None:
        enriched["direction_kind"] = str(direction_kind)
    if status is not None:
        enriched["status"] = str(status)
    if provenance is not None:
        enriched["provenance"] = str(provenance)
    merged_metadata = dict(enriched.get("metadata") or {})
    merged_metadata.update(dict(metadata or {}))
    enriched["metadata"] = merged_metadata
    return enriched


@dataclass(frozen=True)
class StructuralMemberView:
    edge_key: tuple[str, str]
    node_u: str
    node_v: str
    u_xyz: list[float]
    v_xyz: list[float]
    family: str
    force_record: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def length(self):
        dx = self.v_xyz[0] - self.u_xyz[0]
        dy = self.v_xyz[1] - self.u_xyz[1]
        dz = self.v_xyz[2] - self.u_xyz[2]
        return sqrt(dx * dx + dy * dy + dz * dz)

    @property
    def force_status(self):
        return str((self.force_record or {}).get("status") or "unresolved")

    @property
    def force_provenance(self):
        return str((self.force_record or {}).get("provenance") or "graph_derived")

    @property
    def has_semantic_force(self):
        return bool((self.force_record or {}).get("vector"))

    def endpoint_vector_from(self, node_id):
        if str(node_id) == self.node_u:
            return [self.v_xyz[0] - self.u_xyz[0], self.v_xyz[1] - self.u_xyz[1], self.v_xyz[2] - self.u_xyz[2]]
        if str(node_id) == self.node_v:
            return [self.u_xyz[0] - self.v_xyz[0], self.u_xyz[1] - self.v_xyz[1], self.u_xyz[2] - self.v_xyz[2]]
        raise KeyError("Node {0} is not incident to member {1}".format(node_id, self.edge_key))


def build_structural_member_view(graph, edge_key):
    u, v = _ordered_edge_key(edge_key[0], edge_key[1])
    return StructuralMemberView(
        edge_key=(u, v),
        node_u=u,
        node_v=v,
        u_xyz=_node_xyz(graph, u),
        v_xyz=_node_xyz(graph, v),
        family=str(graph.network.edge_attribute((u, v), "family") or "bar"),
        force_record=member_force_record(graph, u, v),
        metadata=_edge_attributes(graph, u, v),
    )
