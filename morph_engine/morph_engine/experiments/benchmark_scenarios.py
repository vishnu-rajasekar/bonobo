from copy import deepcopy


DEFAULT_MITCHELL_PLANAR_BENCHMARK = {
    "scenario_name": "mitchell_planar_benchmark_v1",
    "seed": 42,
    "planar_bounds": {
        "min": [-6.0, -1.0],
        "max": [6.0, 6.0],
    },
    # v1 approximation of a cantilever root region using two fixed support nodes on the left boundary.
    "support_locations": [
        {"node": "0", "xyz": [-5.0, 0.0, 0.0], "fixed": [1, 1, 1]},
        {"node": "1", "xyz": [-5.0, 4.0, 0.0], "fixed": [1, 1, 1]},
    ],
    "load_location": {"node": "2", "xyz": [5.0, 2.0, 0.0]},
    "load_vector": [0.0, -10.0, 0.0],
    "load_magnitude": 10.0,
    "seed_support_to_load_edges": False,
    "max_iterations": 12,
    "enabled_rules": [
        "split_node_rule",
        "extend_node_rule",
        "triangle_closure_rule",
        "loa_intersection_rule",
        "single_node_root_link_rule",
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
    "policy_name": "benchmark_ranked",
    "policy_settings": {},
    "selection_policy": "benchmark_ranked",
}


SECONDARY_TWO_SUPPORT_PLANAR_SANITY = {
    "scenario_name": "two_support_planar_sanity_v1",
    "seed": 42,
    "planar_bounds": {
        "min": [-6.0, -1.0],
        "max": [6.0, 6.0],
    },
    "support_locations": [
        {"node": "0", "xyz": [-5.0, 0.0, 0.0], "fixed": [1, 1, 1]},
        {"node": "1", "xyz": [5.0, 0.0, 0.0], "fixed": [0, 1, 1]},
    ],
    "load_location": {"node": "2", "xyz": [0.0, 4.0, 0.0]},
    "load_vector": [0.0, -10.0, 0.0],
    "load_magnitude": 10.0,
    "seed_support_to_load_edges": True,
    "max_iterations": 12,
    "enabled_rules": list(DEFAULT_MITCHELL_PLANAR_BENCHMARK["enabled_rules"]),
    "rule_settings": deepcopy(DEFAULT_MITCHELL_PLANAR_BENCHMARK["rule_settings"]),
    "evaluator_settings": deepcopy(DEFAULT_MITCHELL_PLANAR_BENCHMARK["evaluator_settings"]),
    "selection_policy": "benchmark_ranked",
}


def get_benchmark_scenario(name="mitchell_planar_benchmark_v1"):
    if name == DEFAULT_MITCHELL_PLANAR_BENCHMARK["scenario_name"]:
        return deepcopy(DEFAULT_MITCHELL_PLANAR_BENCHMARK)
    if name == SECONDARY_TWO_SUPPORT_PLANAR_SANITY["scenario_name"]:
        return deepcopy(SECONDARY_TWO_SUPPORT_PLANAR_SANITY)
    raise ValueError("Unknown benchmark scenario: {0}".format(name))


def get_benchmark_recovery_modes():
    legacy_rules = [
        "split_node_rule",
        "extend_node_rule",
        "triangle_closure_rule",
        "loa_intersection_rule",
    ]

    mode_a = deepcopy(DEFAULT_MITCHELL_PLANAR_BENCHMARK)
    mode_a["scenario_name"] = "mitchell_planar_benchmark_v1_mode_a"
    mode_a["comparison_mode"] = "A"
    mode_a["comparison_label"] = "legacy_active_rules"
    mode_a["enabled_rules"] = list(legacy_rules)

    mode_b = deepcopy(DEFAULT_MITCHELL_PLANAR_BENCHMARK)
    mode_b["scenario_name"] = "mitchell_planar_benchmark_v1_mode_b"
    mode_b["comparison_mode"] = "B"
    mode_b["comparison_label"] = "legacy_rules_plus_resolve_two_forces"
    mode_b["enabled_rules"] = list(legacy_rules) + ["resolve_two_forces_rule"]

    mode_c = deepcopy(DEFAULT_MITCHELL_PLANAR_BENCHMARK)
    mode_c["scenario_name"] = "mitchell_planar_benchmark_v1_mode_c"
    mode_c["comparison_mode"] = "C"
    mode_c["comparison_label"] = "legacy_rules_plus_bidirectional_loa"
    mode_c["enabled_rules"] = [
        "split_node_rule",
        "extend_node_rule",
        "triangle_closure_rule",
        "bidirectional_loa_intersection_rule",
    ]

    mode_d = deepcopy(DEFAULT_MITCHELL_PLANAR_BENCHMARK)
    mode_d["scenario_name"] = "mitchell_planar_benchmark_v1_mode_d"
    mode_d["comparison_mode"] = "D"
    mode_d["comparison_label"] = "legacy_rules_plus_single_node_root_link"
    mode_d["enabled_rules"] = list(legacy_rules) + ["single_node_root_link_rule"]

    return [mode_a, mode_b, mode_c, mode_d]
