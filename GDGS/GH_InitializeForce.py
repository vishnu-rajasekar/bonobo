import rhinoscriptsyntax as rs
import ghpythonlib.components as gh
import Rhino.Geometry as rg
import Rhino as rc
import System.Drawing as sd

import Assembly as assembly
import Grammar as gr
import Rules as r
import GraphicStatics as gs

reload (assembly)
reload (gs)

################################################################################

AppliedForce = gh.Line(Tail, Head) #GH Line Object

################################################################################
# IDENTIFY & ASSIGN

"""
Pass = 0
Support = 1
Load = 2
Float = 3
End = 4
Corner = 5
Tri = 6
Quad = 7
"""

if Type == "1": #Support Point
    ThisNodeType = assembly.NodeType.Support
    ThisForceType = assembly.ForceType.Reaction
    Color = "252, 223,33" #yellow, for support reactions

if Type == "2": #Load Point
    ThisNodeType = assembly.NodeType.Load
    ThisForceType = assembly.ForceType.Applied
    Color = "0, 113, 189" #blue, for applied loads

################################################################################
# CONSTRUCT ASSEMBLY.FORCE

ForceList=[]
Force = assembly.Force(AppliedForce, ThisForceType, -1)
ForceList.append(Force)


Node = assembly.Node(Head, ThisNodeType, ForceList)

Node = gs.RearrangeForces(Node)
Node = gs.EquilibrateNode(Node)
print Node.Forces
################################################################################

"""
print Node.Coordinate
print ThisNodeType
print "Force Head = ", Head
print "Force Tail = ", Tail
print Color 
"""