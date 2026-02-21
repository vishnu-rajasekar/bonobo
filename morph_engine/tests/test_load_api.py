import pytest

from morph_engine.model.structural_graph import StructuralGraph


def test_add_and_get_loads():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[1, 1, 1])
    graph.add_load("0", [0, -10, 0])

    all_loads = graph.get_loads()
    assert len(all_loads) == 1
    assert graph.get_loads("0")[0]["vector"] == [0.0, -10.0, 0.0]


def test_loads_roundtrip():
    graph = StructuralGraph()
    graph.add_node("0", (0, 0, 0), fixed=[1, 1, 1])
    graph.add_load("0", [0, -10, 0])

    data = graph.to_json()
    graph2 = StructuralGraph.from_json(data)

    assert len(graph2.get_loads()) == 1
    assert graph2.get_loads("0")[0]["vector"] == [0.0, -10.0, 0.0]


def test_add_load_missing_node_raises():
    graph = StructuralGraph()

    with pytest.raises(KeyError):
        graph.add_load("0", [0, -10, 0])
