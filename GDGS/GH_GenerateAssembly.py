import rhinoscriptsyntax as rs
import ghpythonlib.components as gh
import Grasshopper as Grasshopper
import Rhino.Geometry as rg
import System.Drawing as sd
import math
import random

import Assembly as assembly
import Grammar as gr
import Rhino as rc
import Rules as rules
import GraphicStatics as gs

reload (assembly)
reload (gs)
reload (rules)
reload (gr)


g = gr.Grammar()
b = gr.RandomComputation(g)
a = b.GenerateRandomAssembly(StartShape)

NUM = 4
bestNum = 5
bestDesigns = []



"""
for i in range(NUM):

    history = []

    
    a = b.GenerateRandomAssembly(StartShape)
    print a
    bestDesigns.append(a)
    
    
    for obj in ghenv.Component.OnPingDocument().Objects:
        if obj.NickName == "MakeAssembly":
            obj.ExpireSolution(False)
    
    
    for t in a.History.Rules:
        c = t[2].Name, "applied at Node", t[0]
        history.append(c)
    
    if len(bestDesigns) < bestNum:
        bestDesigns.append(a)
    else:
        bestDesigns.append(a)
        sorted(bestDesigns, key=lambda a: a.Score, reverse=False)
        bestDesigns.remove(bestDesigns[-1])
        """
