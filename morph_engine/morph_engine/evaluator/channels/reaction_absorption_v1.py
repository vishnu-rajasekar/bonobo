from math import sqrt

from morph_engine.evaluator.base import Channel


class ReactionAbsorptionChannel(Channel):
    name = "reaction_absorption_v1"

    def evaluate(self, graph, context=None):
        reactions_by_node = {}
        total_reaction = [0.0, 0.0, 0.0]
        absorbed_magnitude = 0.0

        for key in graph.network.nodes():
            fixed = graph.network.node_attribute(key, "fixed") or [0, 0, 0]
            temp = graph.get_temp_force(key) or [0, 0, 0]

            if len(fixed) != 3:
                raise ValueError("fixed must be length 3")
            if len(temp) != 3:
                raise ValueError("temp_force must be length 3")

            reaction = [0.0, 0.0, 0.0]
            temp2 = [float(temp[0]), float(temp[1]), float(temp[2])]
            absorbed = False

            for i in range(3):
                if fixed[i] == 1:
                    reaction[i] = -float(temp[i])
                    if float(temp[i]) != 0.0:
                        absorbed = True
                    temp2[i] = 0.0

            if absorbed:
                graph.set_temp_force(key, temp2)

            if reaction != [0.0, 0.0, 0.0]:
                skey = str(key)
                reactions_by_node[skey] = reaction
                total_reaction[0] += reaction[0]
                total_reaction[1] += reaction[1]
                total_reaction[2] += reaction[2]
                absorbed_magnitude += sqrt(
                    reaction[0] * reaction[0]
                    + reaction[1] * reaction[1]
                    + reaction[2] * reaction[2]
                )

        return {
            "valid": True,
            "metrics": {
                "reaction_count": len(reactions_by_node),
                "total_reaction": total_reaction,
                "absorbed_magnitude": absorbed_magnitude,
            },
            "signals": {
                "reactions_by_node": reactions_by_node,
            },
        }
