from dataclasses import dataclass, field


@dataclass
class PolicyNodeObservation:
    node_id: str
    x: float
    y: float
    z: float
    node_kind: str
    degree: int
    active: bool
    temp_force: list[float]
    is_load: bool
    is_support: bool


@dataclass
class PolicyEdgeObservation:
    edge_id: str
    node_u: str
    node_v: str
    length: float
    direction: list[float]
    member_kind: str = "bar"
    force_placeholder: dict = field(default_factory=dict)


@dataclass
class PolicyGlobalObservation:
    phase: str | None
    node_count: int
    edge_count: int
    support_count: int
    load_count: int
    active_front_count: int
    unresolved_force_count: int
    support_connectivity_summary: dict
    plausibility_summary: dict


@dataclass
class PolicyObservation:
    global_features: PolicyGlobalObservation
    node_features: list[PolicyNodeObservation]
    edge_features: list[PolicyEdgeObservation]
    action_mask: list[str] = field(default_factory=list)


def _node_xyz(graph, node_key):
    xyz = graph.network.node_attribute(node_key, "xyz") or [0.0, 0.0, 0.0]
    return [float(xyz[0]), float(xyz[1]), float(xyz[2])]


def _temp_force(graph, node_key):
    return [float(value) for value in (graph.get_temp_force(node_key) or [0.0, 0.0, 0.0])]


def _magnitude(vec):
    return (vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2]) ** 0.5


def _support_nodes(graph):
    supports = []
    for node_key in graph.network.nodes():
        fixed = graph.network.node_attribute(node_key, "fixed") or [0, 0, 0]
        if any(float(value) != 0.0 for value in fixed):
            supports.append(str(node_key))
    return supports


def _load_nodes(graph):
    return sorted({str(load.get("node")) for load in graph.get_loads() if load.get("node") is not None})


def extract_policy_observation(state, applicable_actions=None, phase=None):
    graph = state
    support_nodes = set(_support_nodes(graph))
    load_nodes = set(_load_nodes(graph))

    node_features = []
    active_front_count = 0
    unresolved_force_count = 0
    for node_key in graph.network.nodes():
        skey = str(node_key)
        xyz = _node_xyz(graph, skey)
        temp_force = _temp_force(graph, skey)
        is_support = skey in support_nodes
        is_load = skey in load_nodes
        is_active = _magnitude(temp_force) > 1e-12
        if is_active:
            active_front_count += 1
            unresolved_force_count += 1
        node_kind = "support" if is_support else "load" if is_load else "internal"
        node_features.append(
            PolicyNodeObservation(
                node_id=skey,
                x=xyz[0],
                y=xyz[1],
                z=xyz[2],
                node_kind=node_kind,
                degree=int(graph.network.degree(node_key)),
                active=is_active,
                temp_force=temp_force,
                is_load=is_load,
                is_support=is_support,
            )
        )

    edge_features = []
    for u, v in graph.network.edges():
        su = str(u)
        sv = str(v)
        xyz_u = _node_xyz(graph, su)
        xyz_v = _node_xyz(graph, sv)
        direction = [xyz_v[0] - xyz_u[0], xyz_v[1] - xyz_u[1], xyz_v[2] - xyz_u[2]]
        edge_features.append(
            PolicyEdgeObservation(
                edge_id="{0}-{1}".format(su, sv),
                node_u=su,
                node_v=sv,
                length=_magnitude(direction),
                direction=direction,
            )
        )

    global_features = PolicyGlobalObservation(
        phase=phase,
        node_count=len(node_features),
        edge_count=len(edge_features),
        support_count=len(support_nodes),
        load_count=len(load_nodes),
        active_front_count=active_front_count,
        unresolved_force_count=unresolved_force_count,
        support_connectivity_summary={
            "reachable_support_paths": None,
            "nearest_support_hops": None,
        },
        plausibility_summary={
            "benchmark_plausibility_flag": None,
        },
    )

    return PolicyObservation(
        global_features=global_features,
        node_features=node_features,
        edge_features=edge_features,
        action_mask=[getattr(action, "action_id", getattr(action, "rule_name", "")) for action in (applicable_actions or [])],
    )
