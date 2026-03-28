from .force_ops import bidirected_ray_intersection
from .force_ops import directed_ray_intersection
from .force_ops import flip_temp_force_dir
from .force_ops import get_line_of_action
from .force_ops import get_temp_force
from .force_ops import reverse_force
from .force_ops import transfer_member_force
from .member_ops import get_member_force
from .member_ops import get_member_nodes
from .member_ops import member_length
from .node_ops import connect_two_forces
from .node_ops import connect_two_forces_direct
from .node_ops import equilibrate_node
from .node_ops import find_single_node_root_link_target
from .node_ops import find_closest_link
from .node_ops import find_closest_projection
from .node_ops import get_active_nodes
from .node_ops import rearrange_forces
from .node_ops import resolve_two_forces
from .node_ops import search_connection
from .node_ops import temp_node_equilibrium


VECTOR_GS_OPERATORS = {
    "force": {
        "get_temp_force": get_temp_force,
        "flip_temp_force_dir": flip_temp_force_dir,
        "get_line_of_action": get_line_of_action,
        "transfer_member_force": transfer_member_force,
        "reverse_force": reverse_force,
        "directed_ray_intersection": directed_ray_intersection,
        "bidirected_ray_intersection": bidirected_ray_intersection,
    },
    "node": {
        "get_active_nodes": get_active_nodes,
        "rearrange_forces": rearrange_forces,
        "equilibrate_node": equilibrate_node,
        "temp_node_equilibrium": temp_node_equilibrium,
        "search_connection": search_connection,
        "find_closest_projection": find_closest_projection,
        "find_closest_link": find_closest_link,
        "find_single_node_root_link_target": find_single_node_root_link_target,
        "connect_two_forces": connect_two_forces,
        "connect_two_forces_direct": connect_two_forces_direct,
        "resolve_two_forces": resolve_two_forces,
    },
    "member": {
        "get_member_nodes": get_member_nodes,
        "get_member_force": get_member_force,
        "member_length": member_length,
    },
}
