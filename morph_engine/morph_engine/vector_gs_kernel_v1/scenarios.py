from dataclasses import dataclass
from math import atan2
from math import degrees
from math import radians
from math import tan

from .model import Assembly
from .model import Force
from .model import ForceDirection
from .model import ForceKind
from .model import Node
from .model import NodeType
from .geometry import dot
from .geometry import unit
from .operators import decompose_force_along_directions
from .operators import equilibrate_node


SMOKE_PROBLEM_ID = "concurrent_three_force_smoke_v1"
DIVERSITY_PROBLEM_ID = "michell_diversity_cantilever_v1"


@dataclass(frozen=True)
class ReactionAngleConfiguration:
    """Equilibrium-consistent boundary parameter, independent of policy."""

    configuration_id: str = "reference_reactions_v1"
    lower_support_angle_degrees: float = degrees(atan2(1.0, 3.0))
    minimum_degrees: float = 1.0
    maximum_degrees: float = 33.0

    def __post_init__(self):
        angle = float(self.lower_support_angle_degrees)
        if not self.minimum_degrees <= angle <= self.maximum_degrees:
            raise ValueError(
                "lower support reaction angle is outside its declared admissible range"
            )
        if self.maximum_degrees < self.minimum_degrees:
            raise ValueError("reaction-angle bounds must be ordered")

    def to_data(self):
        return {
            "configuration_id": self.configuration_id,
            "lower_support_angle_degrees": float(
                self.lower_support_angle_degrees
            ),
            "minimum_degrees": float(self.minimum_degrees),
            "maximum_degrees": float(self.maximum_degrees),
        }


def _force_direction(vector, line_direction):
    return ForceDirection.TENSION if dot(vector, line_direction) >= 0.0 else ForceDirection.COMPRESSION


def _make_three_force_scenario(problem_id, reaction_configuration=None):
    reaction_configuration = (
        reaction_configuration or ReactionAngleConfiguration()
    )
    boundary = {"min": [-1.0, -2.0, 0.0], "max": [4.0, 2.0, 0.0]}
    support_a_point = [0.0, -1.0, 0.0]
    support_b_point = [0.0, 1.0, 0.0]
    load_point = [3.0, 0.0, 0.0]
    applied_vector = [0.0, -5.0, 0.0]
    horizontal_run = load_point[0] - support_a_point[0]
    concurrency_point = [
        load_point[0],
        support_a_point[1]
        + horizontal_run
        * tan(radians(reaction_configuration.lower_support_angle_degrees)),
        0.0,
    ]
    if not boundary["min"][1] <= concurrency_point[1] <= boundary["max"][1]:
        raise ValueError("reaction-line concurrency point is outside the scenario boundary")
    direction_a = unit(
        [
            concurrency_point[index] - support_a_point[index]
            for index in range(3)
        ]
    )
    direction_b = unit(
        [
            concurrency_point[index] - support_b_point[index]
            for index in range(3)
        ]
    )
    reactions = decompose_force_along_directions(
        [-component for component in applied_vector],
        direction_a,
        direction_b,
    )
    if reactions is None:
        raise ValueError("Michell benchmark reaction directions must be independent")
    reaction_a = reactions["vector_a"]
    reaction_b = reactions["vector_b"]

    support_a = Node(
        "0",
        support_a_point,
        NodeType.SUPPORT,
        forces=[
            Force(
                support_a_point,
                reaction_a,
                ForceKind.REACTION,
                direction=_force_direction(reaction_a, direction_a),
                metadata={"semantic_origin": "gdgs_boundary_initialization"},
            )
        ],
        active=True,
        metadata={"reaction_direction": direction_a},
    )
    support_b = Node(
        "1",
        support_b_point,
        NodeType.SUPPORT,
        forces=[
            Force(
                support_b_point,
                reaction_b,
                ForceKind.REACTION,
                direction=_force_direction(reaction_b, direction_b),
                metadata={"semantic_origin": "gdgs_boundary_initialization"},
            )
        ],
        active=True,
        metadata={"reaction_direction": direction_b},
    )
    load = Node(
        "2",
        load_point,
        NodeType.LOAD,
        forces=[
            Force(
                load_point,
                applied_vector,
                ForceKind.APPLIED,
                direction=ForceDirection.COMPRESSION,
                metadata={"semantic_origin": "gdgs_boundary_initialization"},
            ),
        ],
        active=True,
    )
    for node in (support_a, support_b, load):
        equilibrate_node(node)

    return Assembly(
        nodes=[support_a, support_b, load],
        members=[],
        boundary=boundary,
        metadata={
            "scenario_name": problem_id,
            "problem_id": problem_id,
            "boundary_force_initialization": "gdgs_equilibrate_node_v1",
            "force_convention": "tail_to_head_vectors_head_to_tail_polygon",
            "benchmark_geometry": {
                "lower_support": support_a_point,
                "upper_support": support_b_point,
                "load_point": load_point,
                "concurrency_point": concurrency_point,
                "applied_load": applied_vector,
                "boundary": boundary,
            },
            "signed_reaction_magnitudes": {
                "0": reactions["scale_a"],
                "1": reactions["scale_b"],
            },
            "reaction_vectors_by_node": {
                "0": reaction_a,
                "1": reaction_b,
            },
            "reaction_directions_by_node": {
                "0": direction_a,
                "1": direction_b,
            },
            "reaction_angle_configuration": {
                **reaction_configuration.to_data(),
                "upper_support_angle_degrees": degrees(
                    atan2(direction_b[1], direction_b[0])
                ),
                "concurrency_point": concurrency_point,
            },
        },
    )


def make_concurrent_three_force_smoke_scenario(reaction_configuration=None):
    return _make_three_force_scenario(SMOKE_PROBLEM_ID, reaction_configuration)


def make_michell_diversity_cantilever_scenario(reaction_configuration=None):
    configuration = reaction_configuration or ReactionAngleConfiguration(
        configuration_id="diversity_reactions_v1",
        lower_support_angle_degrees=27.0,
    )
    return _make_three_force_scenario(DIVERSITY_PROBLEM_ID, configuration)


def make_default_cantilever_scenario(reaction_configuration=None):
    """Retain the original entry point as the smoke-scenario compatibility alias."""
    return make_concurrent_three_force_smoke_scenario(reaction_configuration)
