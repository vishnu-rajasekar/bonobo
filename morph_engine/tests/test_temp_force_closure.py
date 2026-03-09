from morph_engine.evaluator.temp_force_v1 import TempForceChannel
from morph_engine.model.force import Force
from morph_engine.model.force import ForceDirection
from morph_engine.model.force import ForceType
from morph_engine.model.structural_graph import StructuralGraph


def test_balanced_node_produces_no_temp_force():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[0, 0, 0])
    graph.add_force_to_node("0", Force((0, -10, 0), ForceType.LOAD, ForceDirection.COMPRESSION, "0"))
    graph.add_force_to_node("0", Force((0, 10, 0), ForceType.REACTION, ForceDirection.COMPRESSION, "0"))

    channel = TempForceChannel()
    channel.evaluate(graph)

    assert graph.get_temp_force("0") == [0.0, 0.0, 0.0]
    temp_forces = [f for f in graph.get_node_forces("0") if f.type == ForceType.TEMP]
    assert len(temp_forces) == 0


def test_unbalanced_node_produces_correct_temp_force():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[0, 0, 0])
    graph.add_force_to_node("0", Force((0, -10, 0), ForceType.LOAD, ForceDirection.COMPRESSION, "0"))

    channel = TempForceChannel()
    channel.evaluate(graph)

    assert graph.get_temp_force("0") == [0.0, 10.0, 0.0]
    temp_forces = [f for f in graph.get_node_forces("0") if f.type == ForceType.TEMP]
    assert len(temp_forces) == 1
    assert temp_forces[0].vector == (0.0, 10.0, 0.0)


def test_residual_plus_temp_force_is_zero():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[0, 0, 0])
    graph.add_force_to_node("0", Force((4, -3, 0), ForceType.LOAD, ForceDirection.COMPRESSION, "0"))

    channel = TempForceChannel()
    channel.evaluate(graph)

    total = [0.0, 0.0, 0.0]
    for force in graph.get_node_forces("0"):
        total[0] += force.vector[0]
        total[1] += force.vector[1]
        total[2] += force.vector[2]

    assert total == [0.0, 0.0, 0.0]
