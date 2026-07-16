from dataclasses import dataclass
from math import pi

from .geometry import add
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
from .operators import closure_ray_candidate
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
from .operators import structural_completion_reason
from .operators import three_force_closure_hub
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

    def applicable_to(self, assembly, node):
        return node is not None and node.active

    def propose(self, assembly, node, rng):
        return []

    def apply(self, assembly, proposal, rng):
        raise NotImplementedError


class StartGenerationRule(BaseRule):
    name = "StartGeneration"
    weight = 1

    def applicable(self, assembly):
        return assembly.state == GenerationState.START

    def applicable_to(self, assembly, node):
        return self.applicable(assembly)

    def propose(self, assembly, node, rng):
        return [RuleProposal(self.name, [], {}, self.weight)] if self.applicable(assembly) else []

    def apply(self, assembly, proposal, rng):
        assembly.state = GenerationState.GO
        assembly.add_history(self.name, [], {}, {"state": assembly.state})
        return assembly


class CreateNodeRule(BaseRule):
    name = "CreateNode"
    weight = 1

    def __init__(
        self,
        min_length=0.5,
        max_length=1.5,
        min_angle=-0.17,
        max_angle=0.17,
        min_rotation=-pi,
        max_rotation=pi,
        cutoff=4,
        proposal_attempts=16,
    ):
        self.min_length = float(min_length)
        self.max_length = float(max_length)
        self.min_angle = float(min_angle)
        self.max_angle = float(max_angle)
        self.min_rotation = float(min_rotation)
        self.max_rotation = float(max_rotation)
        self.cutoff = int(cutoff)
        self.proposal_attempts = int(proposal_attempts)

    def propose(self, assembly, node, rng):
        if assembly.state != GenerationState.GO or len(assembly.history) >= self.cutoff or not node.active:
            return []
        if get_line_of_action(node) is None:
            return []
        for _ in range(self.proposal_attempts):
            params = {
                "length": rng.uniform(self.min_length, self.max_length),
                "angle": rng.uniform(self.min_angle, self.max_angle),
                "rotation": rng.uniform(self.min_rotation, self.max_rotation),
            }
            if self._candidate(assembly, node, params) is not None:
                return [RuleProposal(self.name, [node.node_id], params, self.weight)]
        return []

    def applicable_to(self, assembly, node):
        return (
            node is not None
            and assembly.state == GenerationState.GO
            and len(assembly.history) < self.cutoff
            and node.active
            and get_line_of_action(node) is not None
        )

    def _candidate(self, assembly, node, params):
        loa = get_line_of_action(node)
        temp = get_temp_force(node)
        if loa is None or temp is None:
            return None
        direction = rotate_z(loa["direction"], params["angle"] + params["rotation"])
        coordinate = add(node.coordinate, scale(direction, params["length"]))
        if not boundary_ok(coordinate, assembly) or assembly.node_exists_at(coordinate):
            return None
        if not segment_is_admissible(
            assembly,
            node.node_id,
            "__create_candidate__",
            node.coordinate,
            coordinate,
        ):
            return None
        return {"coordinate": coordinate, "direction": direction, "temp": temp}

    def apply(self, assembly, proposal, rng):
        node = assembly.node(proposal.target_node_ids[0])
        candidate = self._candidate(assembly, node, proposal.params)
        if candidate is None:
            return assembly
        new_coordinate = candidate["coordinate"]
        member_vector = scale(candidate["direction"], candidate["temp"].magnitude)
        member_force = make_force(
            node.coordinate,
            member_vector,
            ForceKind.MEMBER,
            direction=ForceDirection.TENSION,
            semantic_origin="create_node",
        )
        node.remove_temp_forces()
        node.add_force(member_force)
        equilibrate_node(node)
        new_node = Node(
            node_id=assembly.next_node_id(),
            coordinate=new_coordinate,
            type=NodeType.END,
            forces=[transfer_member_force(member_force, new_coordinate)],
            active=True,
            metadata={"semantic_origin": "create_node"},
        )
        equilibrate_node(new_node)
        assembly.add_node(new_node)
        assembly.add_member(assembly_member_between(assembly, node.node_id, new_node.node_id, member_force))
        assembly.add_history(
            self.name,
            [node.node_id],
            proposal.params,
            {
                "new_node": new_node.node_id,
                "member_force_vector": list(member_force.vector),
                "new_temp_force_vector": list(new_node.get_temp_force().vector),
            },
        )
        return assembly


class ExtendNodeRule(BaseRule):
    name = "ExtendNode"
    weight = 1

    def __init__(self, min_length=0.5, max_length=1.5, cutoff=8):
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
        length = rng.uniform(self.min_length, self.max_length)
        params = {"length": length}
        if self._candidate(assembly, node, params) is None:
            return []
        return [RuleProposal(self.name, [node.node_id], params, self.weight)]

    def applicable_to(self, assembly, node):
        return (
            node is not None
            and assembly.state == GenerationState.GO
            and len(assembly.history) < self.cutoff
            and node.active
            and node.type in {NodeType.FLOAT, NodeType.END, NodeType.CORNER}
            and get_line_of_action(node) is not None
        )

    def _candidate(self, assembly, node, params):
        loa = get_line_of_action(node)
        temp = get_temp_force(node)
        if loa is None or temp is None:
            return None
        new_coordinate = add(node.coordinate, scale(loa["direction"], params["length"]))
        if (
            not boundary_ok(new_coordinate, assembly)
            or assembly.node_exists_at(new_coordinate)
            or not segment_is_admissible(
                assembly,
                node.node_id,
                "__extend_candidate__",
                node.coordinate,
                new_coordinate,
            )
        ):
            return None
        return {"coordinate": new_coordinate, "temp": temp}

    def apply(self, assembly, proposal, rng):
        node = assembly.node(proposal.target_node_ids[0])
        candidate = self._candidate(assembly, node, proposal.params)
        if candidate is None:
            return assembly
        new_coordinate = candidate["coordinate"]
        temp = candidate["temp"]
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
    weight = 1

    def __init__(self, min_length=0.5, max_length=1.5, min_angle=0.17, max_angle=0.52, cutoff=8, proposal_attempts=16):
        self.min_length = float(min_length)
        self.max_length = float(max_length)
        self.min_angle = float(min_angle)
        self.max_angle = float(max_angle)
        self.cutoff = int(cutoff)
        self.proposal_attempts = int(proposal_attempts)

    def propose(self, assembly, node, rng):
        if assembly.state != GenerationState.GO or len(assembly.history) >= self.cutoff or not node.active:
            return []
        if node.type not in {NodeType.SUPPORT, NodeType.LOAD, NodeType.END, NodeType.CORNER}:
            return []
        if get_line_of_action(node) is None:
            return []
        for _ in range(self.proposal_attempts):
            params = {
                "length_a": rng.uniform(self.min_length, self.max_length),
                "length_b": rng.uniform(self.min_length, self.max_length),
                "angle_a": rng.uniform(self.min_angle, self.max_angle),
                "angle_b": -rng.uniform(self.min_angle, self.max_angle),
            }
            if self._candidate(assembly, node, params) is not None:
                return [RuleProposal(self.name, [node.node_id], params, self.weight)]
        return []

    def applicable_to(self, assembly, node):
        return (
            node is not None
            and assembly.state == GenerationState.GO
            and len(assembly.history) < self.cutoff
            and node.active
            and node.type in {NodeType.SUPPORT, NodeType.LOAD, NodeType.END, NodeType.CORNER}
            and get_line_of_action(node) is not None
        )

    def _candidate(self, assembly, node, params):
        temp = get_temp_force(node)
        loa = get_line_of_action(node)
        if temp is None or loa is None:
            return None
        dir_a = rotate_z(loa["direction"], params["angle_a"])
        dir_b = rotate_z(loa["direction"], params["angle_b"])
        decomp = decompose_force_along_directions(temp.vector, dir_a, dir_b)
        if decomp is None:
            return None
        coord_a = add(node.coordinate, scale(dir_a, params["length_a"]))
        coord_b = add(node.coordinate, scale(dir_b, params["length_b"]))
        if not boundary_ok(coord_a, assembly) or not boundary_ok(coord_b, assembly):
            return None
        if assembly.node_exists_at(coord_a) or assembly.node_exists_at(coord_b):
            return None
        if not segment_is_admissible(assembly, node.node_id, "__split_candidate_a__", node.coordinate, coord_a):
            return None
        if not segment_is_admissible(assembly, node.node_id, "__split_candidate_b__", node.coordinate, coord_b):
            return None
        return {
            "temp": temp,
            "decomposition": decomp,
            "coordinate_a": coord_a,
            "coordinate_b": coord_b,
        }

    def apply(self, assembly, proposal, rng):
        node = assembly.node(proposal.target_node_ids[0])
        candidate = self._candidate(assembly, node, proposal.params)
        if candidate is None:
            return assembly
        temp = candidate["temp"]
        decomp = candidate["decomposition"]
        coord_a = candidate["coordinate_a"]
        coord_b = candidate["coordinate_b"]
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

    def applicable_to(self, assembly, node):
        return node is not None and bool(self.propose(assembly, node, None))

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
            and boundary_ok(projection["point"], assembly)
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
        return []

    def applicable_to(self, assembly, node):
        return node is not None and bool(self.propose(assembly, node, None))

    def apply(self, assembly, proposal, rng):
        node = assembly.node(proposal.target_node_ids[0])
        if proposal.params.get("kind") != "projection" or len(proposal.target_node_ids) != 2:
            return assembly
        other = assembly.node(proposal.target_node_ids[1])
        loa_a = get_line_of_action(node)
        loa_b = get_line_of_action(other)
        if loa_a is None or loa_b is None:
            return assembly
        point = proposal.params.get("point") or directed_ray_intersection(
            loa_a["point"], loa_a["direction"], loa_b["point"], loa_b["direction"]
        )
        if point is None or not boundary_ok(point, assembly):
            return assembly
        if connect_two_forces(node, other, assembly, point):
            assembly.add_history(
                self.name,
                [node.node_id, other.node_id],
                proposal.params,
                {"new_projection_node": assembly.nodes[-1].node_id},
            )
        return assembly


class CloseStructureRule(BaseRule):
    name = "CloseStructure"
    weight = 1

    def __init__(self, loopcount=4):
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
            records = []
            ray_combinations = ((1, 1), (1, -1), (-1, 1), (-1, -1))
            chosen_pair = None
            for source_sign, target_sign in ray_combinations:
                combination_candidates = []
                for other in active_nodes(assembly):
                    if other.node_id == node.node_id:
                        continue
                    record = closure_ray_candidate(node, other, assembly, source_sign, target_sign)
                    records.append(record)
                    if record["rejection_reason"] is None:
                        combination_candidates.append(
                            (
                                record["distance_measure"],
                                other.node_id,
                                other,
                                record,
                            )
                        )
                if chosen_pair is None and combination_candidates:
                    chosen_pair = min(combination_candidates, key=lambda item: (item[0], item[1]))
            if chosen_pair is not None:
                _, _, other, chosen = chosen_pair
                return [
                    RuleProposal(
                        self.name,
                        [node.node_id, other.node_id],
                        {
                            "active_count": count,
                            "kind": "progressive_intersection",
                            "point": chosen["intersection"],
                            "ray_combination": [chosen["source_ray_sign"], chosen["target_ray_sign"]],
                            "candidate_intersections": records,
                            "chosen_candidate": chosen,
                        },
                        self.weight,
                    )
                ]
        return []

    def applicable_to(self, assembly, node):
        return node is not None and bool(self.propose(assembly, node, None))

    def apply(self, assembly, proposal, rng):
        nodes = active_nodes(assembly)
        if len(nodes) == 2:
            if resolve_two_forces(assembly) and not active_nodes(assembly):
                reason = structural_completion_reason(assembly)
                assembly.state = GenerationState.END if reason is None else GenerationState.GO
                assembly.metadata["termination_reason"] = "benchmark_complete" if reason is None else reason
                assembly.add_history(
                    self.name,
                    [candidate.node_id for candidate in nodes],
                    proposal.params,
                    {"resolved_two_forces": True, "completion_rejection_reason": reason},
                )
            return assembly
        if proposal.params.get("kind") == "reuse_existing_hub":
            if resolve_three_forces_at_existing_node(assembly) and not active_nodes(assembly):
                reason = structural_completion_reason(assembly)
                assembly.state = GenerationState.END if reason is None else GenerationState.GO
                assembly.metadata["termination_reason"] = "benchmark_complete" if reason is None else reason
                assembly.add_history(
                    self.name,
                    list(proposal.target_node_ids),
                    proposal.params,
                    {"resolved_three_forces_at_existing_node": True, "completion_rejection_reason": reason},
                )
            return assembly
        node = assembly.node(proposal.target_node_ids[0])
        if len(proposal.target_node_ids) != 2:
            return assembly
        other = assembly.node(proposal.target_node_ids[1])
        point = proposal.params.get("point")
        ray_combination = proposal.params.get("ray_combination", [1, 1])
        if point is not None and connect_two_forces(
            node,
            other,
            assembly,
            point,
            source_ray_sign=ray_combination[0],
            target_ray_sign=ray_combination[1],
        ):
            assembly.state = GenerationState.GO
            assembly.metadata.pop("termination_reason", None)
            assembly.add_history(
                self.name,
                [node.node_id, other.node_id],
                proposal.params,
                {"progressive_closure_connection": True},
            )
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

    def applicable_to(self, assembly, node):
        return False

    def apply(self, assembly, proposal, rng):
        reason = structural_completion_reason(assembly)
        assembly.state = GenerationState.END if reason is None else GenerationState.GO
        assembly.metadata["termination_reason"] = "benchmark_complete" if reason is None else reason
        assembly.add_history(self.name, [], proposal.params, {"state": assembly.state, "completion_rejection_reason": reason})
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
