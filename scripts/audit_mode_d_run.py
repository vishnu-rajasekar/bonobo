import json
from pathlib import Path

from morph_engine.model.structural_graph import StructuralGraph


def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _node_xyz(graph, node_key):
    xyz = graph.network.node_attribute(node_key, "xyz") or [0.0, 0.0, 0.0]
    return [float(xyz[0]), float(xyz[1]), float(xyz[2])]


def _vector(a, b):
    return [float(b[0]) - float(a[0]), float(b[1]) - float(a[1]), float(b[2]) - float(a[2])]


def _magnitude(vec):
    return (vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2]) ** 0.5


def _normalize(vec, tolerance=1e-12):
    mag = _magnitude(vec)
    if mag <= tolerance:
        return None
    return [vec[0] / mag, vec[1] / mag, vec[2] / mag]


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _adjacency(graph):
    adjacency = {}
    for node_key in graph.network.nodes():
        adjacency[str(node_key)] = set()
    for u, v in graph.network.edges():
        su = str(u)
        sv = str(v)
        adjacency[su].add(sv)
        adjacency[sv].add(su)
    return adjacency


def _shortest_path(graph, start, goals):
    adjacency = _adjacency(graph)
    frontier = [(str(start), [str(start)])]
    seen = {str(start)}
    goals = {str(goal) for goal in goals}
    while frontier:
        current, path = frontier.pop(0)
        if current in goals:
            return path
        for neighbor in sorted(adjacency.get(current, [])):
            if neighbor in seen:
                continue
            seen.add(neighbor)
            frontier.append((neighbor, path + [neighbor]))
    return None


def _all_node_records(graph):
    records = []
    for node_key in graph.network.nodes():
        records.append(
            {
                "id": str(node_key),
                "xyz": _node_xyz(graph, node_key),
                "fixed": graph.network.node_attribute(node_key, "fixed") or [0, 0, 0],
                "temp_force": graph.get_temp_force(node_key),
            }
        )
    return sorted(records, key=lambda item: item["id"])


def _all_edge_records(graph):
    records = []
    for u, v in graph.network.edges():
        records.append(
            {
                "u": str(u),
                "v": str(v),
                "u_xyz": _node_xyz(graph, u),
                "v_xyz": _node_xyz(graph, v),
            }
        )
    return sorted(records, key=lambda item: (item["u"], item["v"]))


def _support_nodes(graph):
    supports = []
    for node_key in graph.network.nodes():
        fixed = graph.network.node_attribute(node_key, "fixed") or [0, 0, 0]
        if any(float(value) != 0.0 for value in fixed):
            supports.append(str(node_key))
    return sorted(supports)


def _load_nodes(graph):
    return sorted({str(load.get("node")) for load in graph.get_loads() if load.get("node") is not None})


def _choose_suspicious_joint(graph, load_nodes, support_nodes):
    best = None
    for node_key in graph.network.nodes():
        skey = str(node_key)
        neighbors = sorted(str(neighbor) for neighbor in graph.network.neighbors(node_key))
        if len(neighbors) < 2:
            continue
        if skey in load_nodes or skey in support_nodes:
            continue

        vectors = []
        non_collinear = False
        for neighbor in neighbors:
            vec = _vector(_node_xyz(graph, skey), _node_xyz(graph, neighbor))
            unit = _normalize(vec)
            if unit is not None:
                vectors.append({"neighbor": neighbor, "vector": vec, "unit_vector": unit})

        for i in range(len(vectors)):
            for j in range(i + 1, len(vectors)):
                alignment = abs(_dot(vectors[i]["unit_vector"], vectors[j]["unit_vector"]))
                if alignment < 0.999:
                    non_collinear = True
                    break
            if non_collinear:
                break

        if not non_collinear:
            continue

        candidate = {
            "node_id": skey,
            "xyz": _node_xyz(graph, skey),
            "incident_edges": [[skey, neighbor] for neighbor in neighbors],
            "member_vectors": vectors,
        }
        if best is None or len(candidate["incident_edges"]) > len(best["incident_edges"]):
            best = candidate
    return best


def _joint_plausibility(graph, joint, load_nodes, support_nodes, reactions_by_node):
    node_id = joint["node_id"]
    vectors = joint["member_vectors"]
    classifications = []
    non_collinear_pairs = 0
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            alignment = abs(_dot(vectors[i]["unit_vector"], vectors[j]["unit_vector"]))
            is_collinear = alignment >= 0.999
            if not is_collinear:
                non_collinear_pairs += 1
            classifications.append(
                {
                    "neighbors": [vectors[i]["neighbor"], vectors[j]["neighbor"]],
                    "abs_alignment": alignment,
                    "collinear": is_collinear,
                }
            )

    has_external_load = node_id in load_nodes
    has_support = node_id in support_nodes
    reaction = reactions_by_node.get(node_id)
    temp_force = graph.get_temp_force(node_id)
    has_temp_force = _magnitude(temp_force) > 1e-12

    plausibly_equilibrated = True
    apparent_issue = None
    if len(vectors) == 2 and non_collinear_pairs > 0 and not has_external_load and not has_support and not has_temp_force:
        plausibly_equilibrated = False
        apparent_issue = "two_non_collinear_members_without_external_balance"
    elif non_collinear_pairs > 0 and not has_external_load and not has_support and not reaction and not has_temp_force:
        plausibly_equilibrated = False
        apparent_issue = "non_collinear_member_set_without_external_balance"

    return {
        "node_id": node_id,
        "coordinate": joint["xyz"],
        "incident_edges": joint["incident_edges"],
        "load_applied_here": has_external_load,
        "support_applied_here": has_support,
        "temp_force": temp_force,
        "reaction": reaction,
        "member_vectors": [
            {"neighbor": item["neighbor"], "vector": item["vector"]} for item in vectors
        ],
        "pairwise_collinearity": classifications,
        "apparent_unbalanced_perpendicular_component": non_collinear_pairs > 0 and not has_external_load and not has_support,
        "plausibly_equilibrated_under_pin_jointed_axial_reading": plausibly_equilibrated,
        "apparent_issue": apparent_issue,
    }


def main():
    repo_root = Path(__file__).resolve().parent.parent
    comparison = _load_json(repo_root / "experiments" / "benchmark_recovery_comparison.json")
    mode_d = next(item for item in comparison if item.get("mode") == "D")
    run_dir = repo_root / mode_d["run_dir"]

    graph = StructuralGraph.from_json(_load_json(run_dir / "final_graph.json"))
    metrics = _load_json(run_dir / "metrics.json")

    supports = _support_nodes(graph)
    loads = _load_nodes(graph)
    load_node = loads[0] if loads else None
    path = _shortest_path(graph, load_node, supports) if load_node is not None else None
    reactions_by_node = (
        metrics.get("channels", {})
        .get("reaction_absorption_v1", {})
        .get("signals", {})
        .get("reactions_by_node", {})
    )

    suspicious_joint = _choose_suspicious_joint(graph, loads, supports)
    joint_audit = _joint_plausibility(graph, suspicious_joint, loads, supports, reactions_by_node)

    support_records = [{"id": node_id, "xyz": _node_xyz(graph, node_id)} for node_id in supports]
    load_records = [{"id": node_id, "xyz": _node_xyz(graph, node_id)} for node_id in loads]

    verdict = {
        "support_path_exists": path is not None,
        "support_path": path,
        "suspicious_joint_id": suspicious_joint["node_id"],
        "suspicious_joint_plausibly_equilibrated": joint_audit["plausibly_equilibrated_under_pin_jointed_axial_reading"],
        "equilibrium_flag_trustworthy_for_mode_d": False,
        "most_likely_issue": "local_joint_balance_not_checked+support_connectivity_diagnostic_gap",
    }

    payload = {
        "mode_d_run_dir": str(run_dir),
        "part_a_support_path_check": {
            "nodes": _all_node_records(graph),
            "edges": _all_edge_records(graph),
            "support_nodes": support_records,
            "load_nodes": load_records,
            "support_path_exists": path is not None,
            "support_path": path,
            "support_path_note": "Path is graph adjacency through actual edges, not support metadata.",
        },
        "part_b_suspicious_joint_check": joint_audit,
        "part_c_verdict": verdict,
    }

    out_path = repo_root / "experiments" / "mode_d_joint_support_audit.json"
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    print(json.dumps(payload, indent=2))
    print("saved:", out_path)


if __name__ == "__main__":
    main()
