from .base import GSOperator
from .base import edge_length
from .base import has_edge
from .base import node_xyz


GET_MEMBER_NODES = GSOperator("get_member_nodes", notes="Return node ids and endpoint coordinates for a member.")
GET_MEMBER_FORCE = GSOperator(
    "get_member_force",
    notes="Read explicit member force metadata if present. Returns None when Bonobo semantics do not yet carry it.",
)


def get_member_nodes(graph, u, v):
    return {
        "u": str(u),
        "v": str(v),
        "u_xyz": node_xyz(graph, u),
        "v_xyz": node_xyz(graph, v),
    }


def get_member_force(graph, u, v):
    if not has_edge(graph.network, u, v):
        return None

    force = graph.network.edge_attribute((u, v), "force")
    if force is not None:
        return force

    attributes = graph.network.edge_attribute((u, v), "attributes") or {}
    if "force" in attributes:
        return attributes["force"]
    return None


def member_length(graph, u, v):
    return edge_length(graph, u, v)
