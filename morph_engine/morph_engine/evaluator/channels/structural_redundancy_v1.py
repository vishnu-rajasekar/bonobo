from morph_engine.evaluator.base import Channel


class StructuralRedundancyChannel(Channel):
    name = "structural_redundancy_v1"

    def __init__(self, dimension=3):
        self.dimension = dimension

    def evaluate(self, graph):
        j = graph.network.number_of_nodes()
        m = graph.network.number_of_edges()

        r = 0
        for key in graph.network.nodes():
            fixed = graph.network.node_attribute(key, "fixed") or [0, 0, 0]
            r += sum(1 for v in fixed if v)

        if self.dimension == 2:
            redundancy = m + r - 2 * j
        else:
            redundancy = m + r - 3 * j

        return {
            "valid": True,
            "metrics": {
                "joints": j,
                "members": m,
                "reaction_dof": r,
                "redundancy_index": redundancy,
            },
            "signals": {},
        }
