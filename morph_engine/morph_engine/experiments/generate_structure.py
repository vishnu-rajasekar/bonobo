import json
import os
from copy import deepcopy

from morph_engine.evaluator.channels.global_equilibrium_v1 import GlobalEquilibriumChannel
from morph_engine.evaluator.channels.reaction_absorption_v1 import ReactionAbsorptionChannel
from morph_engine.evaluator.channels.unbalanced_force_v1 import UnbalancedForceChannel
from morph_engine.evaluator.evaluator import Evaluator
from morph_engine.experiments.artifacts_v1 import accepted_graph_digest
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
        if su <= sv:
            edges.append((su, sv))
        else:
            edges.append((sv, su))
    return sorted(edges)


def _selected_rule_reason(selection_policy, candidates):
    if not candidates:
        return "no_candidates_available"
    if selection_policy == "first_candidate":
        return "first_candidate_policy"
    return "selected"


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
        if (u, v) in before:
            continue
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
    raise ValueError("Unsupported rule in benchmark scenario: {0}".format(rule_name))


def _rule_counts(rule_sequence):
    counts = {}
    for rule_name in rule_sequence:
        counts[rule_name] = counts.get(rule_name, 0) + 1
    return counts


def _residual_metrics(result):
    global_eq = result.get("channels", {}).get("global_equilibrium_v1", {})
    metrics = global_eq.get("metrics", {})
    return {
        "residual_vector": metrics.get("residual_vector", [0.0, 0.0, 0.0]),
        "residual_magnitude": metrics.get("residual_magnitude", 0.0),
        "global_equilibrium_valid": global_eq.get("valid", False),
    }


def _trace_record(
    iteration,
    graph_before,
    graph_after,
    grammar_state_before,
    grammar_state_after,
    candidates,
    selected_candidate,
    selected_rule_status,
    selected_rule_reason,
    result,
    notes,
):
    candidate_geometry = [candidate_geometry_digest(graph_before, candidate) for candidate in candidates]
    residual = _residual_metrics(result)

    return {
        "iteration": iteration,
        "grammar_state_before": grammar_state_before,
        "grammar_state_after": grammar_state_after,
        "candidate_rule_names": [candidate.rule_name for candidate in candidates],
        "selected_rule": None if selected_candidate is None else selected_candidate.rule_name,
        "selected_rule_status": selected_rule_status,
        "selected_rule_reason": selected_rule_reason,
        "state_id_before": graph_state_id(graph_before),
        "state_id_after": graph_state_id(graph_after),
        "accepted_new_nodes": _accepted_new_nodes(graph_before, graph_after),
        "accepted_new_edges": _accepted_new_edges(graph_before, graph_after),
        "candidate_geometry_count": len(candidate_geometry),
        "candidate_geometry": candidate_geometry,
        "temp_force_count": count_temp_force_nodes(graph_after),
        "residual_vector": residual["residual_vector"],
        "residual_magnitude": residual["residual_magnitude"],
        "global_equilibrium_valid": residual["global_equilibrium_valid"],
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

        support_nodes = [str(item["node"]) for item in self.scenario.get("support_locations", [])]
        load_node = str(load_location["node"])
        for support_node in support_nodes:
            graph.add_edge(support_node, load_node, family="bar")

        load_vector = [float(value) for value in self.scenario.get("load_vector", [0.0, 0.0, 0.0])]
        graph.add_load(load_node, load_vector)
        graph.set_temp_force(load_node, load_vector)
        graph.set_channels_enabled(
            [
                "reaction_absorption_v1",
                "unbalanced_force_v1",
                "global_equilibrium_v1",
            ]
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
        rules = []
        for rule_name in self.scenario.get("enabled_rules", []):
            rules.append(_build_rule(rule_name, rule_settings, self.seed))
        return GrammarEngine(rules)

    def _build_evaluator(self):
        evaluator_settings = self.scenario.get("evaluator_settings", {})
        return Evaluator(
            [
                ReactionAbsorptionChannel(),
                UnbalancedForceChannel(eps=float(evaluator_settings.get("unbalanced_force_eps", 1e-6))),
                GlobalEquilibriumChannel(
                    tolerance=float(evaluator_settings.get("global_equilibrium_tolerance", 1e-6))
                ),
            ]
        )

    def run(self):
        graph = self.initialize_graph()
        grammar = self._build_grammar()
        evaluator = self._build_evaluator()

        trace = []
        rule_sequence = []
        residual_history = []
        node_count_history = []
        edge_count_history = []
        temp_force_count_history = []

        result = evaluator.evaluate(graph)
        self._save_snapshot(graph, 0)

        initial_counts = graph_counts(graph)
        initial_residual = _residual_metrics(result)
        residual_history.append(initial_residual["residual_magnitude"])
        node_count_history.append(initial_counts["node_count"])
        edge_count_history.append(initial_counts["edge_count"])
        temp_force_count_history.append(initial_counts["temp_force_count"])
        trace.append(
            _trace_record(
                iteration=0,
                graph_before=graph,
                graph_after=graph,
                grammar_state_before=str(grammar.state.value),
                grammar_state_after=str(grammar.state.value),
                candidates=[],
                selected_candidate=None,
                selected_rule_status="initial_state",
                selected_rule_reason="baseline_evaluation",
                result=result,
                notes="initial_state",
            )
        )

        selection_policy = self.scenario.get("selection_policy", "first_candidate")

        for step in range(1, self.iterations + 1):
            graph_before = deepcopy(graph)
            state_before = str(grammar.state.value)
            candidates = grammar.propose(graph)
            state_after_propose = str(grammar.state.value)

            if not candidates:
                trace.append(
                    _trace_record(
                        iteration=step,
                        graph_before=graph_before,
                        graph_after=graph,
                        grammar_state_before=state_before,
                        grammar_state_after=state_after_propose,
                        candidates=[],
                        selected_candidate=None,
                        selected_rule_status="not_selected",
                        selected_rule_reason="no_candidates_available",
                        result=result,
                        notes="terminated_no_candidates",
                    )
                )
                break

            if selection_policy != "first_candidate":
                raise ValueError("Unsupported selection policy: {0}".format(selection_policy))

            chosen = candidates[0]
            graph = grammar.apply(graph, chosen)
            result = evaluator.evaluate(graph)
            self._save_snapshot(graph, step)

            counts = graph_counts(graph)
            residual = _residual_metrics(result)
            residual_history.append(residual["residual_magnitude"])
            node_count_history.append(counts["node_count"])
            edge_count_history.append(counts["edge_count"])
            temp_force_count_history.append(counts["temp_force_count"])
            rule_sequence.append(chosen.rule_name)

            trace.append(
                _trace_record(
                    iteration=step,
                    graph_before=graph_before,
                    graph_after=graph,
                    grammar_state_before=state_before,
                    grammar_state_after=state_after_propose,
                    candidates=candidates,
                    selected_candidate=chosen,
                    selected_rule_status="accepted",
                    selected_rule_reason=_selected_rule_reason(selection_policy, candidates),
                    result=result,
                    notes="equilibrium_reached" if residual["global_equilibrium_valid"] else "",
                )
            )

            if residual["global_equilibrium_valid"]:
                break

        descriptors = extract_graph_descriptors(graph)
        accepted_digest = accepted_graph_digest(graph)
        explored_digest = explored_geometry_digest(trace)
        ml_export = export_ml_ready(graph, result)
        structural_dna = {
            "rule_sequence": rule_sequence,
            "rule_counts": _rule_counts(rule_sequence),
            "residual_history": residual_history,
            "node_count_history": node_count_history,
            "edge_count_history": edge_count_history,
            "temp_force_count_history": temp_force_count_history,
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
        }

        artifact_paths = {
            "scenario": self.logger.save_json("scenario.json", self.scenario),
            "config": self.logger.save_config(
                {
                    "iterations": self.iterations,
                    "seed": self.seed,
                    "scenario_name": self.scenario.get("scenario_name"),
                    "selection_policy": selection_policy,
                    "enabled_rules": self.scenario.get("enabled_rules", []),
                    "evaluator_settings": self.scenario.get("evaluator_settings", {}),
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
        }
        summary["artifact_paths"] = artifact_paths
        artifact_paths["summary"] = self.logger.save_json("summary.json", summary)

        run_payload = dict(result)
        run_payload["scenario"] = self.scenario
        run_payload["trace"] = trace
        run_payload["structural_dna"] = structural_dna
        run_payload["graph_descriptors"] = descriptors
        run_payload["accepted_graph_digest"] = accepted_digest
        run_payload["explored_geometry_digest"] = explored_digest
        run_payload["ml_export"] = ml_export
        run_payload["summary"] = summary
        run_payload["artifact_paths"] = artifact_paths

        return graph, run_payload, self.logger.run_dir
