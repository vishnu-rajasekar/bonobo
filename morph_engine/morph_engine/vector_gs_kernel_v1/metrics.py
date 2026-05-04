from collections import Counter

from .geometry import distance
from .model import NodeType


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


def compute_kernel_metrics(assembly, trace=None):
    trace = trace or []
    member_lengths = _member_lengths(assembly)
    support = _support_connectivity(assembly)
    rule_counts = Counter(step.get("rule") for step in trace)

    return {
        "accepted_step_count": len(trace),
        "final_state": assembly.state,
        "final_residual_magnitude": float(assembly.residual_magnitude()),
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
        "equilibrium_reached": float(assembly.residual_magnitude()) <= 1e-9,
        "rule_counts": dict(rule_counts),
    }
