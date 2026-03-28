import json
import os
from copy import deepcopy
import random

from morph_engine.evaluator.channels.global_equilibrium_v1 import GlobalEquilibriumChannel
from morph_engine.evaluator.channels.reaction_absorption_v1 import ReactionAbsorptionChannel
from morph_engine.evaluator.channels.unbalanced_force_v1 import UnbalancedForceChannel
from morph_engine.evaluator.evaluator import Evaluator
from morph_engine.experiments.artifacts_v1 import accepted_graph_digest
from morph_engine.experiments.artifacts_v1 import benchmark_graph_diagnostics
from morph_engine.experiments.artifacts_v1 import candidate_geometry_digest
from morph_engine.experiments.artifacts_v1 import count_temp_force_nodes
from morph_engine.experiments.artifacts_v1 import export_ml_ready
from morph_engine.experiments.artifacts_v1 import explored_geometry_digest
from morph_engine.experiments.artifacts_v1 import extract_graph_descriptors
from morph_engine.experiments.artifacts_v1 import graph_counts
from morph_engine.experiments.artifacts_v1 import graph_state_id
from morph_engine.experiments.benchmark_scenarios import get_benchmark_scenario
from morph_engine.experiments.logger_v1 import ExperimentLogger
from morph_engine.grammar.grammar_engine import GrammarEngine
from morph_engine.grammar.rules.extend_node_rule import ExtendNodeRule
from morph_engine.grammar.rules.loa_intersection_rule import LOAIntersectionRule
from morph_engine.grammar.rules.resolve_two_forces_rule import ResolveTwoForcesRule
from morph_engine.grammar.rules.single_node_root_link_rule import SingleNodeRootLinkRule
from morph_engine.grammar.rules.split_node_rule import SplitNodeRule
from morph_engine.grammar.rules.triangle_closure_rule import TriangleClosureRule
from morph_engine.model.structural_graph import StructuralGraph


def _json_clone(data):
    return json.loads(json.dumps(data))


def _node_xyz(graph, key):
    xyz = graph.network.node_attribute(key, "xyz") or [0.0, 0.0, 0.0]
    return [float(xyz[0]), float(xyz[1]), float(xyz[2])]


def _sorted_edges(graph):
    edges = []
    for u, v in graph.network.edges():
        su = str(u)
        sv = str(v)
        edges.append((su, sv) if su <= sv else (sv, su))
    return sorted(edges)


def _accepted_new_nodes(before_graph, after_graph):
    before = {str(key) for key in before_graph.network.nodes()}
    added = []
    for key in sorted([str(key) for key in after_graph.network.nodes()]):
        if key in before:
            continue
        added.append({"id": key, "xyz": _node_xyz(after_graph, key)})
    return added


def _accepted_new_edges(before_graph, after_graph):
    before = set(_sorted_edges(before_graph))
    added = []
    for u, v in _sorted_edges(after_graph):
        if (u, v) not in before:
            added.append([u, v])
    return added


def _build_rule(rule_name, rule_settings, seed):
    if rule_name == "split_node_rule":
        params = dict(rule_settings.get(rule_name, {}))
        params["seed"] = seed
        return SplitNodeRule(**params)
    if rule_name == "extend_node_rule":
        params = dict(rule_settings.get(rule_name, {}))
        params["seed"] = seed
        return ExtendNodeRule(**params)
    if rule_name == "triangle_closure_rule":
        return TriangleClosureRule(**dict(rule_settings.get(rule_name, {})))
    if rule_name == "loa_intersection_rule":
        return LOAIntersectionRule()
    if rule_name == "bidirectional_loa_intersection_rule":
        return LOAIntersectionRule(bidirectional=True)
    if rule_name == "resolve_two_forces_rule":
        return ResolveTwoForcesRule()
    if rule_name == "single_node_root_link_rule":
        return SingleNodeRootLinkRule()
    raise ValueError("Unsupported rule in benchmark scenario: {0}".format(rule_name))


def _rule_counts(rule_sequence):
    counts = {}
    for rule_name in rule_sequence:
        counts[rule_name] = counts.get(rule_name, 0) + 1
    return counts


def _residual_metrics(result):
    channel = result.get("channels", {}).get("global_equilibrium_v1", {})
    metrics = channel.get("metrics", {})
    return {
        "residual_vector": metrics.get("residual_vector", [0.0, 0.0, 0.0]),
        "residual_magnitude": metrics.get("residual_magnitude", 0.0),
        "global_equilibrium_valid": channel.get("valid", False),
    }


def _source_node(payload):
    for key in ("node", "node_a", "u"):
        value = payload.get(key)
        if value is not None:
            return str(value)
    return None


def _support_metrics_payload(diag_before, diag_after, payload, new_edges):
    source_node = _source_node(payload)
    created_support_connection = False
    support_nodes = set(diag_before["support_node_ids"])
    for u, v in new_edges:
        if u in support_nodes or v in support_nodes:
            created_support_connection = True
            break

    return {
        "source_parent_node": source_node,
        "nearest_support_distance_before": diag_before["nearest_support_distance"],
        "nearest_support_distance_after": diag_after["nearest_support_distance"],
        "created_support_connection": created_support_connection,
        "support_reachable_path_count_before": diag_before["support_reachable_path_count"],
        "support_reachable_path_count_after": diag_after["support_reachable_path_count"],
        "support_connectivity_indicator_before": diag_before["nearest_support_hops"],
        "support_connectivity_indicator_after": diag_after["nearest_support_hops"],
    }


def _candidate_reason_codes(diag_before, diag_after, residual_before, residual_after):
    codes = []
    if not diag_after["inside_bounds"]:
        codes.append("outside_bounds")
    if diag_after["crossing_edge_count"] > 0:
        codes.append("crossing_introduced")
    if diag_after["duplicate_node_count"] > 0:
        codes.append("duplicate_node")
    if diag_after["duplicate_edge_count"] > 0:
        codes.append("duplicate_edge")
    if diag_after["two_member_non_collinear_joint_count"] > 0:
        codes.append("local_joint_non_equilibrated")
    if residual_after > residual_before + 1e-9:
        codes.append("residual_worsened")

    support_distance_improved = _is_better(diag_after["nearest_support_distance"], diag_before["nearest_support_distance"], smaller=True)
    support_hops_improved = _is_better(diag_after["nearest_support_hops"], diag_before["nearest_support_hops"], smaller=True)
    temp_force_improved = diag_after["temp_force_count"] < diag_before["temp_force_count"]
    residual_improved = residual_after < residual_before - 1e-9
    support_reachable_improved = diag_after["support_reachable_path_count"] > diag_before["support_reachable_path_count"]

    if not codes and not any(
        [
            residual_improved,
            support_distance_improved,
            support_hops_improved,
            support_reachable_improved,
            temp_force_improved,
        ]
    ):
        codes.append("no_structural_progress")

    return codes


def _is_better(after, before, smaller):
    if before is None and after is None:
        return False
    if before is None:
        return True
    if after is None:
        return False
    return after < before if smaller else after > before


def _candidate_rank_tuple(diag_before, diag_after, residual_before, residual_after):
    support_distance_delta = 0.0
    if diag_before["nearest_support_distance"] is not None and diag_after["nearest_support_distance"] is not None:
        support_distance_delta = diag_before["nearest_support_distance"] - diag_after["nearest_support_distance"]

    support_hops_delta = 0
    if diag_before["nearest_support_hops"] is not None and diag_after["nearest_support_hops"] is not None:
        support_hops_delta = diag_before["nearest_support_hops"] - diag_after["nearest_support_hops"]

    support_reachable_delta = diag_after["support_reachable_path_count"] - diag_before["support_reachable_path_count"]
    temp_force_delta = diag_before["temp_force_count"] - diag_after["temp_force_count"]
    residual_delta = residual_before - residual_after

    return (
        round(residual_delta, 9),
        round(support_distance_delta, 9),
        support_hops_delta,
        support_reachable_delta,
        temp_force_delta,
        -diag_after["crossing_edge_count"],
        -diag_after["duplicate_node_count"],
        -diag_after["duplicate_edge_count"],
    )


def _diagnostics_bundle(graph, result, bounds):
    diag = benchmark_graph_diagnostics(graph, bounds)
    diag["temp_force_count"] = count_temp_force_nodes(graph)
    diag["residual_magnitude"] = _residual_metrics(result)["residual_magnitude"]
    diag["residual_vector"] = _residual_metrics(result)["residual_vector"]
    diag["global_equilibrium_valid"] = _residual_metrics(result)["global_equilibrium_valid"]
    diag["support_node_ids"] = [str(key) for key in graph.network.nodes() if any(graph.network.node_attribute(key, "fixed") or [0, 0, 0])]
    return diag


def _trace_record(
    iteration,
    graph_before,
    graph_after,
    grammar_state_before,
    grammar_state_after,
    selected_candidate,
    selected_rule_status,
    selected_rule_reason,
    result,
    notes,
    support_metrics,
    candidate_evaluations,
):
    return {
        "iteration": iteration,
        "grammar_state_before": grammar_state_before,
        "grammar_state_after": grammar_state_after,
        "candidate_rule_names": [item["rule_name"] for item in candidate_evaluations],
        "selected_rule": None if selected_candidate is None else selected_candidate.rule_name,
        "selected_rule_status": selected_rule_status,
        "selected_rule_reason": selected_rule_reason,
        "state_id_before": graph_state_id(graph_before),
        "state_id_after": graph_state_id(graph_after),
        "accepted_new_nodes": _accepted_new_nodes(graph_before, graph_after),
        "accepted_new_edges": _accepted_new_edges(graph_before, graph_after),
        "candidate_geometry_count": sum(len(item.get("candidate_geometry", [])) for item in candidate_evaluations),
        "candidate_evaluations": candidate_evaluations,
        "temp_force_count": support_metrics["temp_force_count_after"],
        "temp_force_count_before": support_metrics["temp_force_count_before"],
        "temp_force_count_after": support_metrics["temp_force_count_after"],
        "residual_vector": support_metrics["residual_vector_after"],
        "residual_magnitude": support_metrics["residual_after"],
        "residual_before": support_metrics["residual_before"],
        "residual_after": support_metrics["residual_after"],
        "global_equilibrium_valid": _residual_metrics(result)["global_equilibrium_valid"],
        "source_parent_node": support_metrics["source_parent_node"],
        "nearest_support_distance_before": support_metrics["nearest_support_distance_before"],
        "nearest_support_distance_after": support_metrics["nearest_support_distance_after"],
        "created_support_connection": support_metrics["created_support_connection"],
        "support_reachable_path_count_before": support_metrics["support_reachable_path_count_before"],
        "support_reachable_path_count_after": support_metrics["support_reachable_path_count_after"],
        "support_connectivity_indicator_before": support_metrics["support_connectivity_indicator_before"],
        "support_connectivity_indicator_after": support_metrics["support_connectivity_indicator_after"],
        "notes": notes,
    }


class StructureGenerationExperiment:
    def __init__(self, iterations=None, seed=None, scenario=None, logger=None):
        self.scenario = get_benchmark_scenario() if scenario is None else _json_clone(scenario)
        if seed is not None:
            self.scenario["seed"] = int(seed)
        if iterations is not None:
            self.scenario["max_iterations"] = int(iterations)

        self.iterations = int(self.scenario.get("max_iterations", 20))
        self.seed = int(self.scenario.get("seed", 0))
        self.logger = logger or ExperimentLogger()
        self._rng = random.Random(self.seed)

    def initialize_graph(self):
        graph = StructuralGraph()
        bounds = self.scenario.get("planar_bounds")
        if bounds:
            graph.set_boundary_polygon_xy(
                [
                    [bounds["min"][0], bounds["min"][1]],
                    [bounds["max"][0], bounds["min"][1]],
                    [bounds["max"][0], bounds["max"][1]],
                    [bounds["min"][0], bounds["max"][1]],
                ]
            )

        for support in self.scenario.get("support_locations", []):
            graph.add_node(support["node"], support["xyz"], fixed=support.get("fixed", [1, 1, 1]))

        load_location = self.scenario.get("load_location", {})
        graph.add_node(load_location["node"], load_location["xyz"], fixed=[0, 0, 0])

        load_node = str(load_location["node"])
        if bool(self.scenario.get("seed_support_to_load_edges", False)):
            support_nodes = [str(item["node"]) for item in self.scenario.get("support_locations", [])]
            for support_node in support_nodes:
                graph.add_edge(support_node, load_node, family="bar")

        load_vector = [float(value) for value in self.scenario.get("load_vector", [0.0, 0.0, 0.0])]
        graph.add_load(load_node, load_vector)
        graph.set_temp_force(load_node, load_vector)
        graph.set_channels_enabled(
            ["reaction_absorption_v1", "unbalanced_force_v1", "global_equilibrium_v1"]
        )
        return graph

    def _snapshot_dir(self):
        run_dir = self.logger.create_run_dir()
        path = os.path.join(run_dir, "snapshots")
        os.makedirs(path, exist_ok=True)
        return path

    def _save_snapshot(self, graph, step):
        snapshot_dir = self._snapshot_dir()
        filename = "step_{0:03d}.json".format(int(step))
        with open(os.path.join(snapshot_dir, filename), "w", encoding="utf-8") as handle:
            json.dump(graph.to_json(), handle, indent=2)

    def _build_grammar(self):
        rule_settings = self.scenario.get("rule_settings", {})
        return GrammarEngine([_build_rule(rule_name, rule_settings, self.seed) for rule_name in self.scenario.get("enabled_rules", [])])

    def _build_evaluator(self):
        evaluator_settings = self.scenario.get("evaluator_settings", {})
        return Evaluator(
            [
                ReactionAbsorptionChannel(),
                UnbalancedForceChannel(eps=float(evaluator_settings.get("unbalanced_force_eps", 1e-6))),
                GlobalEquilibriumChannel(tolerance=float(evaluator_settings.get("global_equilibrium_tolerance", 1e-6))),
            ]
        )

    def _evaluate_candidate(self, grammar, evaluator, graph_before, result_before, candidate, bounds):
        candidate_graph = grammar.apply(graph_before, candidate)
        candidate_result = evaluator.evaluate(candidate_graph)
        diag_before = _diagnostics_bundle(graph_before, result_before, bounds)
        diag_after = _diagnostics_bundle(candidate_graph, candidate_result, bounds)
        new_edges = _accepted_new_edges(graph_before, candidate_graph)
        reason_codes = _candidate_reason_codes(
            diag_before,
            diag_after,
            diag_before["residual_magnitude"],
            diag_after["residual_magnitude"],
        )
        admissible = len(reason_codes) == 0

        support_metrics = _support_metrics_payload(diag_before, diag_after, candidate.payload, new_edges)
        support_metrics["temp_force_count_before"] = diag_before["temp_force_count"]
        support_metrics["temp_force_count_after"] = diag_after["temp_force_count"]
        support_metrics["residual_before"] = diag_before["residual_magnitude"]
        support_metrics["residual_after"] = diag_after["residual_magnitude"]
        support_metrics["residual_vector_after"] = diag_after["residual_vector"]

        return {
            "candidate": candidate,
            "graph": candidate_graph,
            "result": candidate_result,
            "diag_before": diag_before,
            "diag_after": diag_after,
            "reason_codes": reason_codes,
            "admissible": admissible,
            "rank_tuple": _candidate_rank_tuple(
                diag_before,
                diag_after,
                diag_before["residual_magnitude"],
                diag_after["residual_magnitude"],
            ),
            "candidate_geometry": [candidate_geometry_digest(graph_before, candidate)],
            "support_metrics": support_metrics,
        }

    def run(self):
        graph = self.initialize_graph()
        grammar = self._build_grammar()
        evaluator = self._build_evaluator()
        bounds = self.scenario.get("planar_bounds")

        trace = []
        rule_sequence = []
        residual_history = []
        node_count_history = []
        edge_count_history = []
        temp_force_count_history = []
        support_distance_history = []
        support_connectivity_history = []

        result = evaluator.evaluate(graph)
        self._save_snapshot(graph, 0)

        initial_counts = graph_counts(graph)
        initial_diag = _diagnostics_bundle(graph, result, bounds)
        residual_history.append(initial_diag["residual_magnitude"])
        node_count_history.append(initial_counts["node_count"])
        edge_count_history.append(initial_counts["edge_count"])
        temp_force_count_history.append(initial_counts["temp_force_count"])
        support_distance_history.append(initial_diag["nearest_support_distance"])
        support_connectivity_history.append(initial_diag["nearest_support_hops"])

        initial_support_metrics = {
            "source_parent_node": None,
            "nearest_support_distance_before": initial_diag["nearest_support_distance"],
            "nearest_support_distance_after": initial_diag["nearest_support_distance"],
            "created_support_connection": False,
            "support_reachable_path_count_before": initial_diag["support_reachable_path_count"],
            "support_reachable_path_count_after": initial_diag["support_reachable_path_count"],
            "support_connectivity_indicator_before": initial_diag["nearest_support_hops"],
            "support_connectivity_indicator_after": initial_diag["nearest_support_hops"],
            "temp_force_count_before": initial_diag["temp_force_count"],
            "temp_force_count_after": initial_diag["temp_force_count"],
            "residual_before": initial_diag["residual_magnitude"],
            "residual_after": initial_diag["residual_magnitude"],
            "residual_vector_after": initial_diag["residual_vector"],
        }
        trace.append(
            _trace_record(
                iteration=0,
                graph_before=graph,
                graph_after=graph,
                grammar_state_before=str(grammar.state.value),
                grammar_state_after=str(grammar.state.value),
                selected_candidate=None,
                selected_rule_status="initial_state",
                selected_rule_reason="baseline_evaluation",
                result=result,
                notes="initial_state",
                support_metrics=initial_support_metrics,
                candidate_evaluations=[],
            )
        )

        selection_policy = self.scenario.get("selection_policy", "benchmark_ranked")
        if selection_policy not in ("benchmark_ranked", "first_candidate", "stochastic_top_band"):
            raise ValueError("Unsupported selection policy: {0}".format(selection_policy))
        termination_reason = "max_iterations_reached"

        for step in range(1, self.iterations + 1):
            graph_before = deepcopy(graph)
            result_before = result
            current_diag = _diagnostics_bundle(graph_before, result_before, bounds)
            current_support_metrics = {
                "source_parent_node": None,
                "nearest_support_distance_before": current_diag["nearest_support_distance"],
                "nearest_support_distance_after": current_diag["nearest_support_distance"],
                "created_support_connection": False,
                "support_reachable_path_count_before": current_diag["support_reachable_path_count"],
                "support_reachable_path_count_after": current_diag["support_reachable_path_count"],
                "support_connectivity_indicator_before": current_diag["nearest_support_hops"],
                "support_connectivity_indicator_after": current_diag["nearest_support_hops"],
                "temp_force_count_before": current_diag["temp_force_count"],
                "temp_force_count_after": current_diag["temp_force_count"],
                "residual_before": current_diag["residual_magnitude"],
                "residual_after": current_diag["residual_magnitude"],
                "residual_vector_after": current_diag["residual_vector"],
            }
            state_before = str(grammar.state.value)
            candidates = grammar.propose_actions(graph)
            state_after_propose = str(grammar.state.value)

            if not candidates:
                termination_reason = "no_candidates_available"
                trace.append(
                    _trace_record(
                        iteration=step,
                        graph_before=graph_before,
                        graph_after=graph,
                        grammar_state_before=state_before,
                        grammar_state_after=state_after_propose,
                        selected_candidate=None,
                        selected_rule_status="not_selected",
                        selected_rule_reason="no_candidates_available",
                        result=result,
                        notes="terminated_no_candidates",
                        support_metrics=current_support_metrics,
                        candidate_evaluations=[],
                    )
                )
                break

            evaluations = [self._evaluate_candidate(grammar, evaluator, graph_before, result_before, candidate, bounds) for candidate in candidates]

            admissible = [item for item in evaluations if item["admissible"]]
            admissible.sort(key=lambda item: item["rank_tuple"], reverse=True)

            chosen_eval = None
            selected_reason = "selected_best_candidate"
            if selection_policy == "first_candidate":
                chosen_eval = evaluations[0]
            elif admissible:
                if selection_policy == "benchmark_ranked":
                    chosen_eval = admissible[0]
                else:
                    top_band_size = max(1, int(self.scenario.get("selection_top_band_size", 2)))
                    top_band = admissible[:top_band_size]
                    chosen_eval = self._rng.choice(top_band)
                    selected_reason = "selected_stochastic_top_band"

            candidate_logs = []
            for item in evaluations:
                candidate = item["candidate"]
                reason_codes = list(item["reason_codes"])
                status = "rejected"
                if chosen_eval is not None and item["candidate"] is chosen_eval["candidate"] and item["admissible"]:
                    status = "accepted"
                    reason_codes = [selected_reason]
                elif item["admissible"] and chosen_eval is not None:
                    reason_codes = ["ranked_lower"]

                candidate_logs.append(
                    {
                        "action_id": getattr(candidate, "action_id", None),
                        "abstract_rule_id": getattr(candidate, "abstract_rule_id", None),
                        "abstract_rule_name": getattr(candidate, "abstract_rule_name", None),
                        "method_family": getattr(candidate, "method_family", None),
                        "rule_name": candidate.rule_name,
                        "payload": dict(candidate.payload),
                        "target_node_ids": list(getattr(candidate, "target_node_ids", []) or []),
                        "target_edge_ids": list(getattr(candidate, "target_edge_ids", []) or []),
                        "operator_strategy": getattr(candidate, "operator_strategy", None),
                        "topology_delta": dict(getattr(candidate, "topology_delta", {}) or {}),
                        "metadata": dict(getattr(candidate, "metadata", {}) or {}),
                        "status": status,
                        "reason_codes": reason_codes,
                        "rank_tuple": list(item["rank_tuple"]),
                        "candidate_geometry": item["candidate_geometry"],
                        "residual_before": item["diag_before"]["residual_magnitude"],
                        "residual_after": item["diag_after"]["residual_magnitude"],
                        "temp_force_count_before": item["diag_before"]["temp_force_count"],
                        "temp_force_count_after": item["diag_after"]["temp_force_count"],
                        "nearest_support_distance_before": item["diag_before"]["nearest_support_distance"],
                        "nearest_support_distance_after": item["diag_after"]["nearest_support_distance"],
                        "support_connectivity_indicator_before": item["diag_before"]["nearest_support_hops"],
                        "support_connectivity_indicator_after": item["diag_after"]["nearest_support_hops"],
                        "support_reachable_path_count_before": item["diag_before"]["support_reachable_path_count"],
                        "support_reachable_path_count_after": item["diag_after"]["support_reachable_path_count"],
                    }
                )

            if chosen_eval is None or not chosen_eval["admissible"]:
                termination_reason = "no_admissible_candidate"
                trace.append(
                    _trace_record(
                        iteration=step,
                        graph_before=graph_before,
                        graph_after=graph,
                        grammar_state_before=state_before,
                        grammar_state_after=state_after_propose,
                        selected_candidate=None,
                        selected_rule_status="not_selected",
                        selected_rule_reason="no_admissible_candidate",
                        result=result,
                        notes="terminated_no_admissible_candidate",
                        support_metrics=current_support_metrics,
                        candidate_evaluations=candidate_logs,
                    )
                )
                break

            graph = chosen_eval["graph"]
            result = chosen_eval["result"]
            self._save_snapshot(graph, step)

            counts = graph_counts(graph)
            diag_after = chosen_eval["diag_after"]
            residual = _residual_metrics(result)
            residual_history.append(residual["residual_magnitude"])
            node_count_history.append(counts["node_count"])
            edge_count_history.append(counts["edge_count"])
            temp_force_count_history.append(counts["temp_force_count"])
            support_distance_history.append(diag_after["nearest_support_distance"])
            support_connectivity_history.append(diag_after["nearest_support_hops"])
            rule_sequence.append(chosen_eval["candidate"].rule_name)

            trace.append(
                _trace_record(
                    iteration=step,
                    graph_before=graph_before,
                    graph_after=graph,
                    grammar_state_before=state_before,
                    grammar_state_after=state_after_propose,
                    selected_candidate=chosen_eval["candidate"],
                    selected_rule_status="accepted",
                    selected_rule_reason=selected_reason,
                    result=result,
                    notes="equilibrium_reached" if residual["global_equilibrium_valid"] else "",
                    support_metrics=chosen_eval["support_metrics"],
                    candidate_evaluations=candidate_logs,
                )
            )

            if residual["global_equilibrium_valid"]:
                termination_reason = "equilibrium_reached"
                break

        descriptors = extract_graph_descriptors(graph)
        accepted_digest = accepted_graph_digest(graph)
        explored_digest = explored_geometry_digest(trace)
        ml_export = export_ml_ready(graph, result)
        final_diag = _diagnostics_bundle(graph, result, bounds)

        accepted_iterations = [item for item in trace if item.get("selected_rule_status") == "accepted"]
        support_trend = {
            "accepted_steps_closer_to_support": sum(
                1
                for item in accepted_iterations
                if _is_better(item.get("nearest_support_distance_after"), item.get("nearest_support_distance_before"), smaller=True)
            ),
            "accepted_steps_farther_from_all_supports": sum(
                1
                for item in accepted_iterations
                if _is_better(item.get("nearest_support_distance_before"), item.get("nearest_support_distance_after"), smaller=True)
            ),
            "accepted_steps_improved_support_connectivity": sum(
                1
                for item in accepted_iterations
                if _is_better(item.get("support_connectivity_indicator_after"), item.get("support_connectivity_indicator_before"), smaller=True)
                or item.get("support_reachable_path_count_after", 0) > item.get("support_reachable_path_count_before", 0)
                or item.get("created_support_connection")
            ),
            "accepted_steps_improved_residual": sum(
                1 for item in accepted_iterations if item.get("residual_after", 0.0) < item.get("residual_before", 0.0) - 1e-9
            ),
        }

        structural_dna = {
            "rule_sequence": rule_sequence,
            "rule_counts": _rule_counts(rule_sequence),
            "residual_history": residual_history,
            "node_count_history": node_count_history,
            "edge_count_history": edge_count_history,
            "temp_force_count_history": temp_force_count_history,
            "support_distance_history": support_distance_history,
            "support_connectivity_history": support_connectivity_history,
        }

        summary = {
            "scenario_name": self.scenario.get("scenario_name"),
            "seed": self.seed,
            "iterations_executed": len(rule_sequence),
            "final_node_count": accepted_digest["node_count"],
            "final_edge_count": accepted_digest["edge_count"],
            "final_temp_force_count": count_temp_force_nodes(graph),
            "final_residual_magnitude": _residual_metrics(result)["residual_magnitude"],
            "global_equilibrium_valid": _residual_metrics(result)["global_equilibrium_valid"],
            "residual_history": residual_history,
            "rule_sequence": rule_sequence,
            "rule_counts": structural_dna["rule_counts"],
            "duplicate_node_count": descriptors["duplicate_node_count"],
            "duplicate_edge_count": descriptors["duplicate_edge_count"],
            "overlapping_edge_count": descriptors["overlapping_edge_count"],
            "crossing_edge_count": descriptors["crossing_edge_count"],
            "two_member_non_collinear_joint_count": final_diag["two_member_non_collinear_joint_count"],
            "support_distance_history": support_distance_history,
            "support_connectivity_history": support_connectivity_history,
            "support_trend": support_trend,
            "termination_reason": termination_reason,
        }

        trace_excerpt = trace[1: min(len(trace), 11)]
        artifact_paths = {
            "scenario": self.logger.save_json("scenario.json", self.scenario),
            "config": self.logger.save_config(
                {
                    "iterations": self.iterations,
                    "seed": self.seed,
                    "scenario_name": self.scenario.get("scenario_name"),
                    "selection_policy": selection_policy,
                    "selection_top_band_size": self.scenario.get("selection_top_band_size"),
                    "enabled_rules": self.scenario.get("enabled_rules", []),
                    "evaluator_settings": self.scenario.get("evaluator_settings", {}),
                    "planar_bounds": bounds,
                }
            ),
            "final_graph": self.logger.save_graph(graph),
            "trace": self.logger.save_trace(trace),
            "metrics": self.logger.save_metrics(result),
            "structural_dna": self.logger.save_json("structural_dna.json", structural_dna),
            "graph_descriptors": self.logger.save_json("graph_descriptors.json", descriptors),
            "accepted_graph_digest": self.logger.save_json("accepted_graph_digest.json", accepted_digest),
            "explored_geometry_digest": self.logger.save_json("explored_geometry_digest.json", explored_digest),
            "ml_export": self.logger.save_json("ml_export.json", ml_export),
            "trace_excerpt": self.logger.save_json("trace_excerpt.json", trace_excerpt),
        }
        summary["artifact_paths"] = artifact_paths
        artifact_paths["summary"] = self.logger.save_json("summary.json", summary)

        run_payload = dict(result)
        run_payload["scenario"] = self.scenario
        run_payload["trace"] = trace
        run_payload["trace_excerpt"] = trace_excerpt
        run_payload["structural_dna"] = structural_dna
        run_payload["graph_descriptors"] = descriptors
        run_payload["accepted_graph_digest"] = accepted_digest
        run_payload["explored_geometry_digest"] = explored_digest
        run_payload["ml_export"] = ml_export
        run_payload["summary"] = summary
        run_payload["artifact_paths"] = artifact_paths

        return graph, run_payload, self.logger.run_dir
