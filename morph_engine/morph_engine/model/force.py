from enum import Enum
from math import sqrt


class ForceType(Enum):
    LOAD = "load"
    REACTION = "reaction"
    MEMBER = "member"
    TEMP = "temp"


class ForceDirection(Enum):
    COMPRESSION = "compression"
    TENSION = "tension"


class Force:
    def __init__(self, vector, type, direction, node_id=None):
        if len(vector) != 3:
            raise ValueError("Force vector must be length 3.")

        self.node_id = None if node_id is None else str(node_id)
        self.vector = (
            float(vector[0]),
            float(vector[1]),
            float(vector[2]),
        )
        self.type = type
        self.direction = direction
        self.magnitude = sqrt(
            self.vector[0] * self.vector[0]
            + self.vector[1] * self.vector[1]
            + self.vector[2] * self.vector[2]
        )

    def normalized_vector(self):
        if self.magnitude < 1e-12:
            return (0.0, 0.0, 0.0)
        return (
            self.vector[0] / self.magnitude,
            self.vector[1] / self.magnitude,
            self.vector[2] / self.magnitude,
        )
