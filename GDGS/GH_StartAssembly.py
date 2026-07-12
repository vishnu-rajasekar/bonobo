import rhinoscriptsyntax as rs
import ghpythonlib.components as ghcomp
import Rhino.Geometry as rg
import Rhino as rc
import Rules as r
import System.Drawing as sd


################################################################################
#  IMPORT JUNEY FILES

import Assembly as assembly
import Grammar as gr

reload(assembly)
################################################################################
#  COMPILE NODES

NodeList = []
NodeList.extend(Loads)
NodeList.extend(Supports)


################################################################################
#  CREATE ASSEMBLY INSTANCE

StartShape = assembly.Assembly(NodeList, [], Boundary)

print StartShape.MyState
print len(StartShape.Nodes)


