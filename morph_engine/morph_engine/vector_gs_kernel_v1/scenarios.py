from .model import Assembly
from .model import Force
from .model import ForceDirection
from .model import ForceKind
from .model import Node
from .model import NodeType


def make_default_cantilever_scenario():
    boundary = {"min": [-6.0, -1.0, 0.0], "max": [6.0, 6.0, 0.0]}
    support_a = Node("0", [-5.0, 0.0, 0.0], NodeType.SUPPORT, forces=[], active=False)
    support_b = Node("1", [-5.0, 4.0, 0.0], NodeType.SUPPORT, forces=[], active=False)
    load = Node(
        "2",
        [5.0, 2.0, 0.0],
        NodeType.LOAD,
        forces=[
            Force([5.0, 2.0, 0.0], [0.0, -10.0, 0.0], ForceKind.APPLIED, direction=ForceDirection.COMPRESSION, metadata={"semantic_origin": "scenario"}),
            Force([5.0, 2.0, 0.0], [0.0, -10.0, 0.0], ForceKind.TEMPORARY, direction=ForceDirection.COMPRESSION, metadata={"semantic_origin": "scenario"}),
        ],
        active=True,
    )
    return Assembly(nodes=[support_a, support_b, load], members=[], boundary=boundary, metadata={"scenario_name": "kernel_cantilever_v1"})

