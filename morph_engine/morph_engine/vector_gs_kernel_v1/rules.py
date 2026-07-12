from dataclasses import dataclass

from .geometry import add
from .geometry import bidirected_ray_intersection
from .geometry import directed_ray_intersection
from .geometry import distance
from .geometry import rotate_z
from .geometry import scale
from .geometry import sub
from .geometry import unit
from .model import ForceDirection
from .model import ForceKind
from .model import GenerationState
from .model import Node
from .model import NodeType
from .operators import active_nodes
from .operators import assembly_member_between
from .operators import boundary_ok
from .operators import closest_link
from .operators import connect_two_forces
from .operators import connection_is_non_degenerate
from .operators import can_resolve_two_forces
from .operators import decompose_force_along_directions
from .operators import equilibrate_node
from .operators import get_line_of_action
from .operators import get_temp_force
from .operators import make_force
from .operators import resolve_two_forces
from .operators import resolve_three_forces_at_existing_node
from .operators import segment_is_admissible
from .operators import three_force_closure_hub
from .operators import support_link_target
from .operators import support_projection_target
from .operators import transfer_member_force


@dataclass
class RuleProposal:
    rule_name: str
    target_node_ids: list[str]
    params: dict
    weight: int


class BaseRule:
    name = "base_rule"
    weight = 1

    def applicable(self, assembly):
        return True

    def propose(self, assembly, node, rng):
        return []

    def apply(self, assembly, proposal, rng):
        raise NotImplementedError


class StartGenerationRule(BaseRule):
    name = "StartGeneration"
    weight = 1

    def applicable(self, assembly):
        return assembly.state == GenerationState.START

    def propose(self, assembly, node, rng):
        return [RuleProposal(self.name, [], {}, self.weight)] if self.applicable(assembly) else []

    def apply(self, assembly, proposal, rng):
        assembly.state = GenerationState.GO
        assembly.add_history(self.name, [], {}, {"state": assembly.state})
        return assembly


class CreateNodeRule(BaseRule):
    name = "CreateNode"
    weight = 1

    def __init__(self, min_length=1.5, max_length=3.0, min_angle=-0.17, max_angle=0.17, cutoff=4):
        self.min_length = float(min_length)
        self.max_length = float(max_length)
        self.min_angle = float(min_angle)
        self.max_angle = float(max_angle)
        self.cutoff = int(cutoff)

    def propose(self, assembly, node, rng):
        if assembly.state != GenerationState.GO or len(assembly.history) >= self.cutoff or not node.active:
            return []
        if get_line_of_action(node) is None:
            return []
        length = rng.uniform(self.min_length, self.max_length)
        angle = rng.uniform(self.min_angle, self.max_angle)
        return [RuleProposal(self.name, [node.node_id], {"length": length, "angle": angle}, self.weight)]

    def apply(self, assembly, proposal, rng):
        node = assembly.node(proposal.target_node_ids[0])
        loa = get_line_of_action(node)
        if loa is None:
            return assembly
        direction = rotate_z(loa["direction"], proposal.params["angle"])
        new_coordinate = add(node.coordinate, scale(direction, proposal.params["length"]))
        if not boundary_ok(new_coordinate, assembly) or assembly.node_exists_at(new_coordinate):
            return assembly
        new_node = Node(
            node_id=assembly.next_node_id(),
            coordinate=new_coordinate,
            type=NodeType.FLOAT,
            forces=[],
            active=True,
            metadata={"semantic_origin": "create_node"},
        )
        assembly.add_node(new_node)
        assembly.add_history(self.name, [node.node_id], proposal.params, {"new_node": new_node.node_id})
        return assembly


class ExtendNodeRule(BaseRule):
    name = "ExtendNode"
    weight = 1

    def __init__(self, min_length=1.5, max_length=3.0, cutoff=8):
        self.min_length = float(min_length)
        self.max_length = float(max_length)
        self.cutoff = int(cutoff)

    def propose(self, assembly, node, rng):
        if assembly.state != GenerationState.GO or len(assembly.history) >= self.cutoff or not node.active:
            return []
        if node.type not in {NodeType.FLOAT, NodeType.END, NodeType.CORNER}:
            return []
        if get_line_of_action(node) is None:
            return []
        return [RuleProposal(self.name, [node.node_id], {"length": rng.uniform(self.min_length, self.max_length)}, self.weight)]

    def apply(self, assembly, proposal, rng):
        node = assembly.node(proposal.target_node_ids[0])
        loa = get_line_of_action(node)
        temp = get_temp_force(node)
        if loa is None or temp is None:
            return assembly
        new_coordinate = add(node.coordinate, scale(loa["direction"], proposal.params["length"]))
        if not boundary_ok(new_coordinate, assembly) or assembly.node_exists_at(new_coordinate):
            return assembly
        member_force = make_force(node.coordinate, temp.vector, ForceKind.MEMBER, direction=temp.direction, semantic_origin="extend_node")
        node.remove_temp_forces()
        node.add_force(member_force)
        node.active = False
        new_node = Node(
            node_id=assembly.next_node_id(),
            coordinate=new_coordinate,
            type=NodeType.END,
            forces=[transfer_member_force(member_force, new_coordinate)],
            active=True,
            metadata={"semantic_origin": "extend_node"},
        )
        equilibrate_node(new_node)
        assembly.add_node(new_node)
        assembly.add_member(assembly_member_between(assembly, node.node_id, new_node.node_id, member_force))
        assembly.add_history(self.name, [node.node_id], proposal.params, {"new_node": new_node.node_id})
        return assembly


class SplitNodeRule(BaseRule):
    name = "SplitNode"
    weight = 5

    def __init__(self, min_length=2.0, max_length=4.5, min_angle=0.17, max_angle=0.52, cutoff=8):
        self.min_length = float(min_length)
        self.max_length = float(max_length)
        self.min_angle = float(min_angle)
        self.max_angle = float(max_angle)
        self.cutoff = int(cutoff)

    def propose(self, assembly, node, rng):
        if assembly.state != GenerationState.GO or len(assembly.history) >= self.cutoff or not node.active:
            return []
        if node.type not in {NodeType.SUPPORT, NodeType.LOAD, NodeType.END, NodeType.CORNER}:
            return []
        if get_line_of_action(node) is None:
            return []
        return [
            RuleProposal(
                self.name,
                [node.node_id],
                {
                    "length_a": rng.uniform(self.min_length, self.max_length),
                    "length_b": rng.uniform(self.min_length, self.max_length),
                    "angle_a": rng.uniform(self.min_angle, self.max_angle),
                    "angle_b": -rng.uniform(self.min_angle, self.max_angle),
                },
                self.weight,
            )
        ]

    def apply(self, assembly, proposal, rng):
        node = assembly.node(proposal.target_node_ids[0])
        temp = get_temp_force(node)
        loa = get_line_of_action(node)
        if temp is None or loa is None:
            return assembly
        dir_a = rotate_z(loa["direction"], proposal.params["angle_a"])
        dir_b = rotate_z(loa["direction"], proposal.params["angle_b"])
        decomp = decompose_force_along_directions(temp.vector, dir_a, dir_b)
        if decomp is None:
            return assembly
        coord_a = add(node.coordinate, scale(dir_a, proposal.params["length_a"]))
        coord_b = add(node.coordinate, scale(dir_b, proposal.params["length_b"]))
        if not boundary_ok(coord_a, assembly) or not boundary_ok(coord_b, assembly):
            return assembly
        if assembly.node_exists_at(coord_a) or assembly.node_exists_at(coord_b):
            return assembly
        force_a = make_force(node.coordinate, decomp["vector_a"], ForceKind.MEMBER, direction=temp.direction, semantic_origin="split_node", branch="a")
        force_b = make_force(node.coordinate, decomp["vector_b"], ForceKind.MEMBER, direction=temp.direction, semantic_origin="split_node", branch="b")
        node.remove_temp_forces()
        node.add_force(force_a)
        node.add_force(force_b)
        node.active = False
        new_node_a = Node(assembly.next_node_id(), coord_a, NodeType.END, [transfer_member_force(force_a, coord_a)], True, {"semantic_origin": "split_node"})
        equilibrate_node(new_node_a)
        assembly.add_node(new_node_a)
        new_node_b = Node(assembly.next_node_id(), coord_b, NodeType.END, [transfer_member_force(force_b, coord_b)], True, {"semantic_origin": "split_node"})
        equilibrate_node(new_node_b)
        assembly.add_node(new_node_b)
        assembly.add_member(assembly_member_between(assembly, node.node_id, new_node_a.node_id, force_a))
        assembly.add_member(assembly_member_between(assembly, node.node_id, new_node_b.node_id, force_b))
        assembly.add_history(self.name, [node.node_id], proposal.params, {"new_nodes": [new_node_a.node_id, new_node_b.node_id]})
        return assembly


class ConnectTwoNodesRule(BaseRule):
    name = "ConnectTwoNodes"
    weight = 1

    def __init__(self, radius=10.0, factor=0.5):
        self.radius = float(radius)
        self.factor = float(factor)

    def propose(self, assembly, node, rng):
        if assembly.state != GenerationState.GO or not node.active:
            return []
        others = [other for other in active_nodes(assembly) if other.node_id != node.node_id]
        proposals = []
        for other in others:
            if distance(node.coordinate, other.coordinate) <= self.radius and segment_is_admissible(
                assembly,
                node.node_id,
                other.node_id,
                node.coordinate,
                other.coordinate,
            ):
                proposals.append(RuleProposal(self.name, [node.node_id, other.node_id], {"factor": self.factor}, self.weight))
        return proposals[:1]

    def apply(self, assembly, proposal, rng):
        node1 = assembly.node(proposal.target_node_ids[0])
        node2 = assembly.node(proposal.target_node_ids[1])
        temp1 = get_temp_force(node1)
        temp2 = get_temp_force(node2)
        if temp1 is None or temp2 is None or not segment_is_admissible(
            assembly,
            node1.node_id,
            node2.node_id,
            node1.coordinate,
            node2.coordinate,
        ):
            return assembly
        mag1 = temp1.magnitude
        mag2 = temp2.magnitude
        amplitude = min(mag1, mag2) + abs(mag1 - mag2) * proposal.params["factor"]
        connector_1 = unit(sub(node2.coordinate, node1.coordinate))
        connector_2 = unit(sub(node1.coordinate, node2.coordinate))
        if connector_1 is None or connector_2 is None:
            return assembly
        force1 = make_force(node1.coordinate, scale(connector_1, amplitude), ForceKind.MEMBER, direction=ForceDirection.COMPRESSION, semantic_origin="connect_two_nodes")
        force2 = make_force(node2.coordinate, scale(connector_2, amplitude), ForceKind.MEMBER, direction=ForceDirection.COMPRESSION, semantic_origin="connect_two_nodes")
        node1.remove_temp_forces()
        node2.remove_temp_forces()
        node1.add_force(force1)
        node2.add_force(force2)
        node1.active = True
        node2.active = True
        equilibrate_node(node1)
        equilibrate_node(node2)
        assembly.add_member(assembly_member_between(assembly, node1.node_id, node2.node_id, force1))
        assembly.add_history(self.name, [node1.node_id, node2.node_id], proposal.params, {"member_added": True})
        return assembly


class ExtendAndConnectTwoNodesRule(BaseRule):
    name = "ExtendAndConnectTwoNodes"
    weight = 1

    def __init__(self, radius=10.0):
        self.radius = float(radius)

    def propose(self, assembly, node, rng):
        if assembly.state != GenerationState.GO or not node.active:
            return []
        projection = closest_link(node, assembly)
        if (
            projection is not None
            and projection["distance"] <= self.radius
            and connection_is_non_degenerate(node, projection["other"], assembly, projection["point"])
        ):
            return [
                RuleProposal(
                    self.name,
                    [node.node_id, projection["other"].node_id],
                    {"kind": "projection", "point": projection["point"]},
                    self.weight,
                )
            ]
        support_target = support_link_target(node, assembly)
        if support_target is not None:
            return [RuleProposal(self.name, [node.node_id, support_target["support"].node_id], {"kind": "support"}, self.weight)]
        projection_point = support_projection_target(node, assembly)
        if projection_point is not None:
            return [RuleProposal(self.name, [node.node_id], {"kind": "root_projection", "point": projection_point}, self.weight)]
        return []

    def apply(self, assembly, proposal, rng):
        kind = proposal.params["kind"]
        node = assembly.node(proposal.target_node_ids[0])
        if kind == "projection" and len(proposal.target_node_ids) == 2:
            other = assembly.node(proposal.target_node_ids[1])
            loa_a = get_line_of_action(node)
            loa_b = get_line_of_action(other)
            if loa_a is None or loa_b is None:
                return assembly
            point = proposal.params.get("point") or directed_ray_intersection(loa_a["point"], loa_a["direction"], loa_b["point"], loa_b["direction"])
            if point is None or not boundary_ok(point, assembly):
                return assembly
            if connect_two_forces(node, other, assembly, point):
                assembly.add_history(self.name, [node.node_id, other.node_id], proposal.params, {"new_projection_node": True})
            return assembly
        if kind == "support" and len(proposal.target_node_ids) == 2:
            support = assembly.node(proposal.target_node_ids[1])
            temp = get_temp_force(node)
            if temp is None or assembly.member_between(node.node_id, support.node_id):
                return assembly
            member_force = make_force(node.coordinate, sub(support.coordinate, node.coordinate), ForceKind.MEMBER, direction=ForceDirection.COMPRESSION, semantic_origin="extend_and_connect_support")
            node.remove_temp_forces()
            node.add_force(member_force)
            node.active = False
            support.add_force(transfer_member_force(member_force, support.coordinate))
            support.active = False
            assembly.add_member(assembly_member_between(assembly, node.node_id, support.node_id, member_force))
            assembly.add_history(self.name, [node.node_id, support.node_id], proposal.params, {"support_link": True})
            return assembly
        if kind == "root_projection":
            point = list(proposal.params["point"])
            if not boundary_ok(point, assembly) or assembly.node_exists_at(point):
                return assembly
            temp = get_temp_force(node)
            if temp is None:
                return assembly
            member_force = make_force(node.coordinate, temp.vector, ForceKind.MEMBER, direction=temp.direction, semantic_origin="extend_and_connect_projection")
            node.remove_temp_forces()
            node.add_force(member_force)
            node.active = False
            new_node = Node(assembly.next_node_id(), point, NodeType.FLOAT, [transfer_member_force(member_force, point)], True, {"semantic_origin": "root_projection"})
            equilibrate_node(new_node)
            assembly.add_node(new_node)
            assembly.add_member(assembly_member_between(assembly, node.node_id, new_node.node_id, member_force))
            assembly.add_history(self.name, [node.node_id], proposal.params, {"new_node": new_node.node_id})
        return assembly


class CloseStructureRule(BaseRule):
    name = "CloseStructure"
    weight = 30

    def __init__(self, loopcount=0):
        self.loopcount = int(loopcount)

    def propose(self, assembly, node, rng):
        if len(assembly.history) <= self.loopcount:
            return []
        if not node.active:
            return []
        count = len(active_nodes(assembly))
        if count == 2:
            if can_resolve_two_forces(assembly):
                return [RuleProposal(self.name, [node.node_id], {"active_count": count}, self.weight)]
            return []
        if count == 3:
            hub = three_force_closure_hub(assembly)
            if hub is not None:
                return [
                    RuleProposal(
                        self.name,
                        [hub.node_id],
                        {"active_count": count, "kind": "reuse_existing_hub"},
                        self.weight,
                    )
                ]
        if count >= 3:
            for other in active_nodes(assembly):
                if other.node_id == node.node_id:
                    continue
                loa_a = get_line_of_action(node)
                loa_b = get_line_of_action(other)
                if loa_a is None or loa_b is None:
                    continue
                point = bidirected_ray_intersection(loa_a["point"], loa_a["direction"], loa_b["point"], loa_b["direction"])
                if point is not None and boundary_ok(point, assembly) and connection_is_non_degenerate(node, other, assembly, point):
                    return [
                        RuleProposal(
                            self.name,
                            [node.node_id, other.node_id],
                            {"active_count": count, "point": point},
                            self.weight,
                        )
                    ]
        return []

    def apply(self, assembly, proposal, rng):
        nodes = active_nodes(assembly)
        if len(nodes) == 2:
            if resolve_two_forces(assembly) and not active_nodes(assembly):
                assembly.state = GenerationState.END
                assembly.add_history(self.name, [candidate.node_id for candidate in nodes], proposal.params, {"resolved_two_forces": True})
            return assembly
        if proposal.params.get("kind") == "reuse_existing_hub":
            if resolve_three_forces_at_existing_node(assembly) and not active_nodes(assembly):
                assembly.state = GenerationState.END
                assembly.add_history(
                    self.name,
                    list(proposal.target_node_ids),
                    proposal.params,
                    {"resolved_three_forces_at_existing_node": True},
                )
            return assembly
        node = assembly.node(proposal.target_node_ids[0])
        if len(proposal.target_node_ids) != 2:
            return assembly
        other = assembly.node(proposal.target_node_ids[1])
        point = proposal.params.get("point")
        if point is not None and connect_two_forces(node, other, assembly, point):
            assembly.state = GenerationState.CLOSE
            assembly.add_history(self.name, [node.node_id, other.node_id], proposal.params, {"closure_connection": True})
        return assembly


class EndGenerationRule(BaseRule):
    name = "EndGeneration"
    weight = 1

    def __init__(self, max_steps=20):
        self.max_steps = int(max_steps)

    def propose(self, assembly, node, rng):
        if len(assembly.history) >= self.max_steps or not active_nodes(assembly):
            return [RuleProposal(self.name, [], {"max_steps": self.max_steps}, self.weight)]
        return []

    def apply(self, assembly, proposal, rng):
        assembly.state = GenerationState.END
        assembly.add_history(self.name, [], proposal.params, {"state": assembly.state})
        return assembly


def default_rules():
    return [
        StartGenerationRule(),
        CreateNodeRule(),
        ExtendNodeRule(),
        SplitNodeRule(),
        ConnectTwoNodesRule(),
        ExtendAndConnectTwoNodesRule(),
        CloseStructureRule(),
        EndGenerationRule(),
    ]
