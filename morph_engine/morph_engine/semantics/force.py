from dataclasses import dataclass, field
from math import sqrt
from typing import Any


def vector_magnitude(vec3):
    return sqrt(float(vec3[0]) * float(vec3[0]) + float(vec3[1]) * float(vec3[1]) + float(vec3[2]) * float(vec3[2]))


def normalize_vector(vec3, tolerance=1e-12):
    magnitude = vector_magnitude(vec3)
    if magnitude <= tolerance:
        return None
    return [float(vec3[0]) / magnitude, float(vec3[1]) / magnitude, float(vec3[2]) / magnitude]


@dataclass(frozen=True)
class StructuralForce:
    force_id: str
    kind: str
    vector: list[float]
    direction_kind: str | None = None
    source_node: str | None = None
    target_node: str | None = None
    related_member: tuple[str, str] | None = None
    line_of_action_point: list[float] | None = None
    status: str = "explicit"
    provenance: str = "graph_derived"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def magnitude(self):
        return vector_magnitude(self.vector)

    @property
    def direction(self):
        return normalize_vector(self.vector)

    @property
    def line_of_action(self):
        if self.line_of_action_point is None or self.direction is None:
            return None
        return {
            "point": list(self.line_of_action_point),
            "direction": list(self.direction),
        }

    @property
    def signed_magnitude(self):
        if self.direction_kind == "compression":
            return -self.magnitude
        if self.direction_kind == "tension":
            return self.magnitude
        return self.magnitude
