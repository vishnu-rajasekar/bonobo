from copy import deepcopy


DEFAULT_MITCHELL_PLANAR_BENCHMARK = {
    "scenario_name": "mitchell_planar_benchmark_v1",
    "seed": 42,
    "planar_bounds": {
        "min": [-6.0, -1.0],
        "max": [6.0, 6.0],
    },
    "support_locations": [
        {"node": "0", "xyz": [-5.0, 0.0, 0.0], "fixed": [1, 1, 1]},
        {"node": "1", "xyz": [5.0, 0.0, 0.0], "fixed": [1, 1, 1]},
    ],
    "load_location": {"node": "2", "xyz": [0.0, 4.0, 0.0]},
    "load_vector": [10.0, 0.0, 0.0],

    "load_magnitude": 10.0,
    "max_iterations": 12,
    "enabled_rules": [
        "split_node_rule",
        "extend_node_rule",
        "triangle_closure_rule",
        "loa_intersection_rule",
    ],
    "rule_settings": {
        "split_node_rule": {"theta_min": 0.35, "theta_max": 0.65, "length": 2.0},
        "extend_node_rule": {"lmin": 1.0, "lmax": 2.0},
        "triangle_closure_rule": {"radius": 6.0},
        "loa_intersection_rule": {},
    },
    "evaluator_settings": {
        "unbalanced_force_eps": 1e-6,
        "global_equilibrium_tolerance": 1e-6,
    },
    "selection_policy": "first_candidate",
}


def get_benchmark_scenario(name="mitchell_planar_benchmark_v1"):
    if name != DEFAULT_MITCHELL_PLANAR_BENCHMARK["scenario_name"]:
        raise ValueError("Unknown benchmark scenario: {0}".format(name))
    return deepcopy(DEFAULT_MITCHELL_PLANAR_BENCHMARK)
