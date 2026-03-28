import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import Rhino.DocObjects as rd
import System.Drawing as sd
import copy_reg as copy
import ghpythonlib.components as gh
import random
import math
import copy

import scriptcontext
################################################################################
#  IMPORT JUNEY FILES
################################################################################

import Rules as rules
import RandomUtility as ru
import GraphicStatics as gs
reload (gs)


################################################################################
#  FORCE
################################################################################

class Force:
    def __init__(self, line, type, direction):
        self.Line = line # rhino 3DVector, (x,y,z)  
        self.Type = type # 
        self.Direction = direction #boolean. by default, a force is not a member.

class ForceType(object):
    Pass = 0
    Reaction = 1
    Applied = 2
    Temporary = 3
    Member = 4

class ForceDirection(object):
    Compression = -1
    Tension = 1


################################################################################
#  NODE
################################################################################

class Node:
    def __init__(self, coordinate, type, forces):
        self.Coordinate = coordinate # (x,y,z)
        self.Type = type # number.
        self.Forces = forces #List of all forces on the node
        self.NodeState = NodeState.Go

class NodeType(object):
    Pass = 0
    Support = 1
    Load = 2
    Float = 3
    End = 4
    Corner = 5
    Tri = 6
    Quad = 7

class NodeState(object):
    Pass = 0
    Go = 1


################################################################################
#  ASSEMBLY
################################################################################

class Assembly:
    def __init__(self, nodes, members, boundary): # boundary = [x,y]
        self.Name = "StartName"
        self.Number = 0
        self.Nodes = nodes
        self.Boundary = boundary
        self.MyState = rules.State.Start
        self.History = RuleHistory()
        self.Members = members #list of members (lines)
        self.Score = 0
        self.Length = 0 
        self.MCount = 0
        self.OrderKey = 0
        self.RxnAngle = 0
        scriptcontext.sticky['initial_assembly'] = copy.deepcopy(self)

    def RandomNodePicker(self):
        gonodes = []
        for i in range (0,len(self.Nodes)):
            if self.Nodes[i].NodeState == 1:
                gonodes.append(self.Nodes[i])
            else:
                pass
        
        loadsupportnodes = []
        for i in range (0,len(self.Nodes)):
            if self.Nodes[i].NodeState == 1:
                if self.Nodes[i].Type == 1 or self.Nodes[i].Type == 2:
                    loadsupportnodes.append(self.Nodes[i])
                else:
                    pass
            else:
                pass
        #print ('load and supports', len(loadsupportnodes))
        
        numNodes1 = len(loadsupportnodes)
        if numNodes1 == 0:
            pass
        else:
            randNode1 = loadsupportnodes[ru.MyRandom.Btwn(0, numNodes1-1)] #randint could choose the bounds... so need -1
            #print ('random support', gs.GetNodeIndex(randNode1, self))
        
        numNodes = len(gonodes)
        randNode = gonodes[ru.MyRandom.Btwn(0, numNodes-1)] #randint could choose the bounds... so need -1
        return randNode

    def RearrangeNodes(self):
        SortOrder = []
        
        for i in range(0, len(self.Nodes)):#first, sort support points
            SupportNodeList = []
            SupportNodeLabel = []
            if self.Nodes[i].Type == 1: 
                SupportNodeList.append(self.Nodes[i])
                SupportNodeLabel.append(i)
            SupportNodeSortOrder = gh.SortPoints(SupportNodeList)[1]
            SupportOrder = [SupportNodeLabel[j] for j in SupportNodeSortOrder]
            for k in SupportOrder:
                SortOrder.append(k)
        
        for i in range(0, len(self.Nodes)):#second, sort load points
            LoadNodeList = []
            LoadNodeLabel = []
            if self.Nodes[i].Type == 2: 
                LoadNodeList.append(self.Nodes[i])
                LoadNodeLabel.append(i)
            LoadNodeSortOrder = gh.SortPoints(LoadNodeList)[1]
            LoadOrder = [LoadNodeLabel[j] for j in LoadNodeSortOrder]
            for k in LoadOrder:
                SortOrder.append(k)
        
        for i in range(0, len(self.Nodes)):#sort all other points
            OtherNodeList = []
            OtherNodeLabel = []
            if self.Nodes[i].Type == 2: 
                OtherNodeList.append(self.Nodes[i])
                OtherNodeLabel.append(i)
            OtherNodeSortOrder = gh.SortPoints(OtherNodeList)[1]
            OtherOrder = [OtherNodeLabel[j] for j in OtherNodeSortOrder]
            for k in OtherOrder:
                SortOrder.append(k)
        self.Nodes = [self.Nodes[j] for j in SortOrder]

    def GetScore(self):
        memberlength=[]
        memberforceamplitude = []
        memberforcetype = []
        score = 0
        for member in self.Members:
            length = gh.Length(member)
            amplitude = gs.GetMemberForce(member, self)[0]
            score += length*amplitude
        
        return score

    def GetLength(self):
        memberlength=[]
        totallength = 0
        for member in self.Members:
            length = gh.Length(member)
            totallength += length
        
        return totallength


################################################################################
#OTHER

class RuleHistory:
    def __init__(self):
        self.Rules = []
        
    def AddRule(self, nodeindex, node, rule, params):
        self.Rules.append((nodeindex, node, rule, params))