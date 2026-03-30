from copy import deepcopy
from dataclasses import dataclass, field

from .geometry import add
from .geometry import magnitude
from .geometry import sub
from .geometry import unit


class ForceKind:
    REACTION = "reaction"
    APPLIED = "applied"
    TEMPORARY = "temporary"
    MEMBER = "member"


class ForceDirection:
    COMPRESSION = -1
    TENSION = 1


class NodeType:
    SUPPORT = "support"
    LOAD = "load"
    FLOAT = "float"
    END = "end"
    CORNER = "corner"
    TRI = "tri"
    QUAD = "quad"


class GenerationState:
    START = "start"
    GO = "go"
    CLOSE = "close"
    END = "end"


@dataclass
class Force:
    point: list[float]
    vector: list[float]
    kind: str
    direction: int = ForceDirection.COMPRESSION
    related_member: str | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def magnitude(self):
        return magnitude(self.vector)

    @property
    def line_of_action_direction(self):
        return unit(self.vector)

    def to_data(self):
        return {
            "point": list(self.point),
            "vector": list(self.vector),
            "kind": self.kind,
            "direction": self.direction,
            "related_member": self.related_member,
            "metadata": dict(self.metadata),
        }


@dataclass
class Node:
    node_id: str
    coordinate: list[float]
    type: str
    forces: list[Force] = field(default_factory=list)
    active: bool = True
    metadata: dict = field(default_factory=dict)

    def temp_forces(self):
        return [force for force in self.forces if force.kind == ForceKind.TEMPORARY]

    def member_forces(self):
        return [force for force in self.forces if force.kind == ForceKind.MEMBER]

    def get_temp_force(self):
        temps = self.temp_forces()
        return temps[0] if temps else None

    def remove_temp_forces(self):
        self.forces = [force for force in self.forces if force.kind != ForceKind.TEMPORARY]

    def add_force(self, force):
        self.forces.append(force)

    def local_resultant(self):
        total = [0.0, 0.0, 0.0]
        for force in self.forces:
            total = add(total, force.vector)
        return total

    def to_data(self):
        return {
            "node_id": self.node_id,
            "coordinate": list(self.coordinate),
            "type": self.type,
            "active": bool(self.active),
            "metadata": dict(self.metadata),
            "forces": [force.to_data() for force in self.forces],
        }


@dataclass
class Member:
    member_id: str
    start_node: str
    end_node: str
    force: Force | None = None
    metadata: dict = field(default_factory=dict)

    def to_data(self):
        return {
            "member_id": self.member_id,
            "start_node": self.start_node,
            "end_node": self.end_node,
            "force": None if self.force is None else self.force.to_data(),
            "metadata": dict(self.metadata),
        }


@dataclass
class RuleApplication:
    step_index: int
    rule_name: str
    target_node_ids: list[str]
    params: dict
    summary: dict

    def to_data(self):
        return {
            "step_index": self.step_index,
            "rule_name": self.rule_name,
            "target_node_ids": list(self.target_node_ids),
            "params": dict(self.params),
            "summary": dict(self.summary),
        }


@dataclass
class Assembly:
    nodes: list[Node]
    members: list[Member]
    boundary: dict
    state: str = GenerationState.START
    history: list[RuleApplication] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def clone(self):
        return deepcopy(self)

    def node(self, node_id):
        for node in self.nodes:
            if node.node_id == str(node_id):
                return node
        raise KeyError(node_id)

    def active_nodes(self):
        return [node for node in self.nodes if node.active and node.get_temp_force() is not None]

    def support_nodes(self):
        return [node for node in self.nodes if node.type == NodeType.SUPPORT]

    def load_nodes(self):
        return [node for node in self.nodes if node.type == NodeType.LOAD]

    def node_exists_at(self, coordinate, tolerance=1e-9):
        for node in self.nodes:
            if magnitude(sub(node.coordinate, coordinate)) <= tolerance:
                return True
        return False

    def add_node(self, node):
        self.nodes.append(node)
        return node

    def add_member(self, member):
        self.members.append(member)
        return member

    def next_node_id(self):
        used = {node.node_id for node in self.nodes}
        index = 0
        while True:
            candidate = str(index)
            if candidate not in used:
                return candidate
            index += 1

    def next_member_id(self):
        return "m{0}".format(len(self.members))

    def member_between(self, node_a, node_b):
        a = str(node_a)
        b = str(node_b)
        for member in self.members:
            if {member.start_node, member.end_node} == {a, b}:
                return member
        return None

    def add_history(self, rule_name, target_node_ids, params, summary):
        self.history.append(
            RuleApplication(
                step_index=len(self.history),
                rule_name=rule_name,
                target_node_ids=[str(node_id) for node_id in target_node_ids],
                params=dict(params),
                summary=dict(summary),
            )
        )

    def residual_magnitude(self):
        total = 0.0
        for node in self.active_nodes():
            temp = node.get_temp_force()
            if temp is not None:
                total += temp.magnitude
        return total

    def to_data(self):
        return {
            "state": self.state,
            "boundary": dict(self.boundary),
            "metadata": dict(self.metadata),
            "nodes": [node.to_data() for node in self.nodes],
            "members": [member.to_data() for member in self.members],
            "history": [item.to_data() for item in self.history],
            "residual_magnitude": self.residual_magnitude(),
        }
