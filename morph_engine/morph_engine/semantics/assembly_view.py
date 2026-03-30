from dataclasses import dataclass, field

from .node import StructuralNodeView
from .member import StructuralMemberView


@dataclass(frozen=True)
class StructuralAssemblyView:
    nodes: dict[str, StructuralNodeView]
    members: dict[tuple[str, str], StructuralMemberView]
    support_node_ids: list[str] = field(default_factory=list)
    load_node_ids: list[str] = field(default_factory=list)

    @property
    def active_front_ids(self):
        return [node_id for node_id, node in self.nodes.items() if node.active]

    @property
    def support_nodes(self):
        return [self.nodes[node_id] for node_id in self.support_node_ids if node_id in self.nodes]

    @property
    def load_nodes(self):
        return [self.nodes[node_id] for node_id in self.load_node_ids if node_id in self.nodes]

    @property
    def semantically_resolved_node_ids(self):
        return [node_id for node_id, node in self.nodes.items() if node.equilibrium_summary()["closed"]]

    def node(self, node_id):
        return self.nodes[str(node_id)]

    def member(self, u, v):
        su = str(u)
        sv = str(v)
        key = (su, sv) if su <= sv else (sv, su)
        return self.members[key]
