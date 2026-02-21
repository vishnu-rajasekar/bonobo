from morph_engine.evaluator.base import Channel


class GeometryPlanarChannel(Channel):
    name = "geometry_planar_v1"

    def evaluate(self, graph):
        network = graph.network
        return {
            "valid": True,
            "metrics": {
                "node_count": network.number_of_nodes(),
                "edge_count": network.number_of_edges(),
            },
            "signals": {},
        }
