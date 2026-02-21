from morph_engine.evaluator.base import Channel


class MaxwellCountChannel(Channel):
    name = "maxwell_v1"

    def evaluate(self, graph):
        network = graph.network
        j = network.number_of_nodes()
        b = network.number_of_edges()

        r = 0
        for node in network.nodes():
            fixed = network.node_attribute(node, "fixed") or [0, 0, 0]
            r += sum(1 for dof in fixed if dof)

        redundancy = b - (3 * j - r)

        return {
            "valid": True,
            "metrics": {
                "node_count": j,
                "edge_count": b,
                "restrained_dof": r,
                "redundancy_proxy": redundancy,
            },
            "signals": {
                "redundancy_proxy": redundancy,
            },
        }
