import Rhino
import scriptcontext as sc
from registry import register_tool

sc.doc = Rhino.RhinoDoc.ActiveDoc


@register_tool("draw_network")
def draw_network(nodes, edges):

    # Clear document before redraw
    sc.doc.Objects.Clear()

    # Draw nodes
    for key, data in nodes.items():
        pt = Rhino.Geometry.Point3d(*data["xyz"])
        sc.doc.Objects.AddPoint(pt)

    # Draw edges
    for u, v in edges:
        pu = Rhino.Geometry.Point3d(*nodes[str(u)]["xyz"])
        pv = Rhino.Geometry.Point3d(*nodes[str(v)]["xyz"])
        line = Rhino.Geometry.Line(pu, pv)
        sc.doc.Objects.AddLine(line)

    sc.doc.Views.ActiveView.ActiveViewport.ZoomExtents()
    sc.doc.Views.Redraw()

    return {"status": "drawn"}
