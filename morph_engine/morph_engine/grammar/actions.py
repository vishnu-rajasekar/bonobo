import hashlib
import json
from dataclasses import dataclass, field

from morph_engine.grammar.base import Candidate


@dataclass
class GrammarAction:
    action_id: str
    abstract_rule_id: str | None
    abstract_rule_name: str | None
    method_family: str
    implementation_rule_name: str
    target_node_ids: list[str] = field(default_factory=list)
    target_edge_ids: list[list[str]] = field(default_factory=list)
    operator_strategy: str | None = None
    parameter_payload: dict = field(default_factory=dict)
    topology_delta: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    @property
    def rule_name(self):
        return self.implementation_rule_name

    @property
    def payload(self):
        return self.parameter_payload

    def to_json(self):
        return {
            "action_id": self.action_id,
            "abstract_rule_id": self.abstract_rule_id,
            "abstract_rule_name": self.abstract_rule_name,
            "method_family": self.method_family,
            "implementation_rule_name": self.implementation_rule_name,
            "target_node_ids": list(self.target_node_ids),
            "target_edge_ids": [list(edge) for edge in self.target_edge_ids],
            "operator_strategy": self.operator_strategy,
            "parameter_payload": dict(self.parameter_payload),
            "topology_delta": dict(self.topology_delta),
            "metadata": dict(self.metadata),
        }


class Action(Candidate):
    """Backward-compatible alias for a concrete rule application."""


def make_action(rule_name, payload):
    return Action(rule_name, payload)


def _stable_action_id(implementation_rule_name, payload):
    stable_payload = json.dumps(payload, sort_keys=True, default=str)
    digest = hashlib.sha1(stable_payload.encode("utf-8")).hexdigest()[:12]
    return "{0}:{1}".format(implementation_rule_name, digest)


def _extract_target_node_ids(payload):
    node_ids = []
    for key, value in payload.items():
        key_text = str(key)
        if "node" in key_text and value is not None:
            node_ids.append(str(value))
        if key_text in {"u", "v"} and value is not None:
            node_ids.append(str(value))
    return sorted(set(node_ids))


def _extract_target_edge_ids(payload):
    if payload.get("u") is not None and payload.get("v") is not None:
        return [[str(payload["u"]), str(payload["v"])]]
    return []


def coerce_to_grammar_action(action, method_family="vector_gs", abstract_rule_id=None, abstract_rule_name=None):
    from morph_engine.grammar.vector_gs.rules import get_vector_gs_rule_binding

    payload = dict(getattr(action, "payload", {}) or {})
    implementation_rule_name = str(getattr(action, "rule_name"))
    binding = get_vector_gs_rule_binding(implementation_rule_name=implementation_rule_name)
    resolved_abstract_rule_id = abstract_rule_id or getattr(binding, "abstract_rule_id", None)
    resolved_abstract_rule_name = abstract_rule_name or getattr(binding, "abstract_rule_name", None) or resolved_abstract_rule_id

    return GrammarAction(
        action_id=_stable_action_id(implementation_rule_name, payload),
        abstract_rule_id=resolved_abstract_rule_id,
        abstract_rule_name=resolved_abstract_rule_name,
        method_family=getattr(binding, "method_family", method_family),
        implementation_rule_name=implementation_rule_name,
        target_node_ids=_extract_target_node_ids(payload),
        target_edge_ids=_extract_target_edge_ids(payload),
        operator_strategy=getattr(binding, "operator_strategy", None) or implementation_rule_name,
        parameter_payload=payload,
        topology_delta=dict(getattr(binding, "topology_delta_summary", {}) or {}),
        metadata={
            "binding_status": getattr(binding, "status", None),
            "binding_provisional": getattr(binding, "provisional", None),
            "binding_notes": getattr(binding, "notes", None),
        },
    )
