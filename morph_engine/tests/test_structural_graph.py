from morph_engine.model.structural_graph import StructuralGraph


def test_roundtrip():
    g = StructuralGraph()
    g.add_node("0", (0, 0, 0), fixed=(True, True, True))
    g.add_node("1", (5, 0, 0))
    g.add_edge("0", "1")

    data = g.to_json()
    g2 = StructuralGraph.from_json(data)

    assert g2.network.number_of_nodes() == 2
    assert g2.network.number_of_edges() == 1

def test_schema_v03_roundtrip():
    g = StructuralGraph()

    g.set_profile("planar_truss")
    g.set_assumptions(dimension=3, behavior="axial_only")
    g.set_boundary_polygon_xy([(0,0),(10,0),(10,5),(0,5)])
    g.set_channels_enabled(["geometry_planar_v1"])

    g.add_node("0", (0,0,0), fixed=[1,1,1])
    g.add_node("1", (5,0,0), fixed=[0,0,0])
    g.add_edge("0","1", family="bar")

    data = g.to_json()
    g2 = StructuralGraph.from_json(data)

    assert g2.profile == "planar_truss"
    assert g2.assumptions["dimension"] == 3
    assert g2.boundary["type"] == "polygon_xy"
    # assert len(g2.nodes["0"]["fixed"]) == 3
    fixed = g2.network.node_attribute("0", "fixed")
    assert len(fixed) == 3

    # assert g2.edges[0]["family"] == "bar"
    family = g2.network.edge_attribute(("0", "1"), "family")
    assert family == "bar"

