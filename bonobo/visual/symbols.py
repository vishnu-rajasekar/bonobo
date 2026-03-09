from compas.geometry import Circle
from compas.geometry import Frame
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Vector


LOAD_COLOR = (55 / 255, 126 / 255, 227 / 255)      # #377EE3
REACTION_COLOR = (84 / 255, 165 / 255, 71 / 255)  # #54A547
TEMP_COLOR = (0.6, 0.2, 0.8)


def _unit_vector(vec):
    v = Vector(*vec)
    if v.length < 1e-9:
        return None
    return v.unitized()


def _add(viewer, obj, **kwargs):
    if hasattr(viewer, "add") and callable(getattr(viewer, "add")):
        return viewer.add(obj, **kwargs)
    return viewer.scene.add(obj, **kwargs)


def add_force_arrow(viewer, xyz, vector, scale=1.0, kind="load"):
    """
    Draws force arrow using head-position semantics.

    Compression -> arrow head at node
    Tension     -> arrow tail at node
    """

    direction = _unit_vector(vector)
    if direction is None:
        return

    magnitude = Vector(*vector).length
    length = magnitude * scale

    node_point = Point(*xyz)

    if kind == "load":
        color = LOAD_COLOR
        # Load assumed compressive: head at node.
        end = node_point
        start = end - direction * length
    elif kind == "reaction":
        color = REACTION_COLOR
        # Compression default for reactions until signed axial data is available.
        end = node_point
        start = end - direction * length
    elif kind == "temp":
        color = TEMP_COLOR
        end = node_point
        start = end - direction * length
    else:
        return

    # Render in COMPAS viewer vector-anchor style.
    # For compression semantics, head is at `end` (node), tail at `start`.
    arrow_vector = Vector(end.x - start.x, end.y - start.y, end.z - start.z)
    _add(
        viewer,
        arrow_vector,
        anchor=start,
        linecolor=color,
        name=f"{kind}_arrow",
    )


def add_support_symbol(viewer, xyz, scale=1.0):
    """
    Support = circle + triangle.
    Node is top vertex of triangle and center of circle.
    """

    # Robust unpack for list/tuple-like xyz inputs.
    x = float(xyz[0])
    y = float(xyz[1])
    z = float(xyz[2])
    center = Point(x, y, z)

    # COMPAS-compatible circle construction: Circle(Plane(origin, normal), radius)
    plane = Plane(center, Vector(0, 0, 1))
    frame = Frame(plane.point, Vector(1, 0, 0), Vector(0, 1, 0))
    circle = Circle(0.15 * scale, frame)
    _add(viewer, circle, color=(0, 0, 0), name="Support")

    h = 0.4 * scale
    w = 0.3 * scale

    p1 = center
    p2 = Point(x - w, y - h, z)
    p3 = Point(x + w, y - h, z)

    triangle = Polygon([p1, p2, p3])
    _add(viewer, triangle, color=(0, 0, 0), name="Support")
