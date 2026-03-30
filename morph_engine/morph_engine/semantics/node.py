from dataclasses import dataclass, field
from math import atan2

from .force import StructuralForce
from .force import normalize_vector
from .force import vector_magnitude


@dataclass(frozen=True)
class StructuralNodeView:
    node_id: str
    xyz: list[float]
    node_kind: str
    degree: int
    incident_member_ids: list[tuple[str, str]]
    local_forces: list[StructuralForce] = field(default_factory=list)
    support: bool = False
    load: bool = False

    @property
    def temp_forces(self):
        return [force for force in self.local_forces if force.kind == "temporary"]

    @property
    def member_forces(self):
        return [force for force in self.local_forces if force.kind == "member"]

    @property
    def external_forces(self):
        return [force for force in self.local_forces if force.kind in {"load", "reaction"}]

    @property
    def non_temporary_forces(self):
        return [force for force in self.local_forces if force.kind != "temporary"]

    @property
    def active(self):
        return self.unresolved_force_magnitude > 1e-12

    @property
    def unresolved_force_vector(self):
        if not self.temp_forces:
            return [0.0, 0.0, 0.0]
        total = [0.0, 0.0, 0.0]
        for force in self.temp_forces:
            total[0] += float(force.vector[0])
            total[1] += float(force.vector[1])
            total[2] += float(force.vector[2])
        return total

    @property
    def local_balance_vector(self):
        total = [0.0, 0.0, 0.0]
        for force in self.local_forces:
            total[0] += float(force.vector[0])
            total[1] += float(force.vector[1])
            total[2] += float(force.vector[2])
        return total

    @property
    def local_balance_magnitude(self):
        return vector_magnitude(self.local_balance_vector)

    @property
    def preferred_unresolved_force_vector(self):
        if self.unresolved_force_magnitude > 1e-12:
            return self.unresolved_force_vector
        return self.local_balance_vector

    @property
    def unresolved_force_magnitude(self):
        return vector_magnitude(self.unresolved_force_vector)

    @property
    def active_line_of_action(self):
        direction = normalize_vector(self.preferred_unresolved_force_vector)
        if direction is None:
            return None
        return {
            "point": list(self.xyz),
            "direction": direction,
        }

    @property
    def equilibrium_related_force_count(self):
        return len(self.local_forces)

    def equilibrium_summary(self, tolerance=1e-12):
        balance = self.local_balance_vector
        closing = [-balance[0], -balance[1], -balance[2]]
        return {
            "balance_vector": balance,
            "balance_magnitude": vector_magnitude(balance),
            "closing_vector": closing,
            "closed": vector_magnitude(balance) <= tolerance,
            "force_count": len(self.local_forces),
        }

    def local_force_arrangement(self):
        def sort_key(force):
            direction = force.direction or [0.0, 0.0, 0.0]
            angle = atan2(float(direction[1]), float(direction[0]))
            return (-round(angle, 9), force.kind, force.force_id)

        return sorted(self.local_forces, key=sort_key)
