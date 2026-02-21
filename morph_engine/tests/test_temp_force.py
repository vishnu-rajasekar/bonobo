from morph_engine.model.structural_graph import StructuralGraph


def test_temp_force_roundtrip():
    g = StructuralGraph()
    g.add_node("0", (0, 0, 0), fixed=[1, 1, 1])
    g.set_temp_force("0", [1.25, -2.5, 3.75])

    data = g.to_json()
    g2 = StructuralGraph.from_json(data)

    temp_force = g2.get_temp_force("0")
    assert len(temp_force) == 3
    assert temp_force == [1.25, -2.5, 3.75]
