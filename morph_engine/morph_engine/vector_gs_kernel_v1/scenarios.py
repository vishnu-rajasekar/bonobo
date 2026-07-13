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


def _force_direction(vector, line_direction):
    return ForceDirection.TENSION if dot(vector, line_direction) >= 0.0 else ForceDirection.COMPRESSION


def _make_three_force_scenario(problem_id):
    boundary = {"min": [-1.0, -2.0, 0.0], "max": [4.0, 2.0, 0.0]}
    support_a_point = [0.0, -1.0, 0.0]
    support_b_point = [0.0, 1.0, 0.0]
    load_point = [3.0, 0.0, 0.0]
    applied_vector = [0.0, -5.0, 0.0]
    direction_a = unit([load_point[index] - support_a_point[index] for index in range(3)])
    direction_b = unit([load_point[index] - support_b_point[index] for index in range(3)])
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
                "concurrency_point": load_point,
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
        },
    )


def make_concurrent_three_force_smoke_scenario():
    return _make_three_force_scenario(SMOKE_PROBLEM_ID)


def make_michell_diversity_cantilever_scenario():
    return _make_three_force_scenario(DIVERSITY_PROBLEM_ID)


def make_default_cantilever_scenario():
    """Retain the original entry point as the smoke-scenario compatibility alias."""
    return make_concurrent_three_force_smoke_scenario()
