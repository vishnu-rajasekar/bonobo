import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import Rhino.DocObjects as rd
import System.Drawing as sd

import ghpythonlib.components as gh
import random
import math
from itertools import permutations


################################################################################
#  IMPORT JUNEY FILES
################################################################################

import Assembly as assembly
import RandomUtility as ru
import GraphicStatics as gs

reload (assembly)
reload (gs)

#2015 04 29


################################################################################
#  Rule Parameters
################################################################################
# Angle in radians

cutoff = 4
loopcount = 4

rule0weight = 1

rule1weight = 0
rule1minL = 2
rule1maxL = 5
rule1minA1 = -10*(math.pi/180)
rule1maxA1 = 10*(math.pi/180)
rule1minA2 = 0*(math.pi/180)
rule1maxA2 = 359*(math.pi/180)

rule2weight = 1
rule2minL = 2
rule2maxL = 5

rule3weight = 5
rule3minL = 4
rule3maxL = 8
rule3minA = 10*(math.pi/180)
rule3maxA = 30*(math.pi/180)

rule4weight = 1
rule4radius = 10

rule5weight = 1
rule5radius = 10

rule6weight = 30

rule7weight = 0


################################################################################
#  STATE
################################################################################

class State(object):
    Start = 1
    Go = 2
    Close = 3
    End = 4


################################################################################
#  RULE TYPE
################################################################################

class Type(object):
    Start = 0
    Create = 1
    Connect = 2
    Merge = 3
    Close = 4


################################################################################
#  RULE - BASE
################################################################################
class BaseRule:

    def __init__(self):
        self.MyGrammar = None
        self.Name = "No Name"
        self.Description = "No Description"
        self.Params = []

    def CanApply(self, currentshape):
        raise NotImplementedError

    def CanApplyNode(self, node):
        raise NotImplementedError

    def Apply(self, currentshape, params, node):
        raise NotImplementedError

    def UpdateHistory(self, currentshape, params, node):
        nodeindex = gs.GetNodeIndex (node, currentshape)
        currentshape.History.AddRule(nodeindex, node, self, params)


################################################################################
#  RULE - PARAM
################################################################################
class RuleParam:

    def __init__(self, lb, ub, name):
        self.Min = lb
        self.Max = ub
        self.Name = name

    def GetRandomValue(self):
        val = ru.MyRandom.Float(self.Min, self.Max)
        return val
    



################################################################################
#  RULE 0 - GO STATE
################################################################################
class Rule0(BaseRule):

    def __init__(self):
        self.Name = "Rule 0: 'START'"
        self.Description = "This is the zeroth test rule."
        self.Params = [RuleParam(0, 1, "P1"), RuleParam(0, 1, "P2")]
        self.Weight = 1

    def CanApply(self, assembly):
        if assembly.MyState == State.Start:
            return True
        else:
            return False

    def CanApplyNode(self, node): 
        #Node level condition
        return True

    def Apply(self, currentshape, params, node):
        currentshape.MyState = State.Go
        self.UpdateHistory(currentshape, params, node)
        return currentshape


################################################################################
#  RULE 1 - CREATE NODE
################################################################################
class Rule1(BaseRule):

    def __init__(self):
        self.Name = "Rule 1: 'Create Node'"
        self.Description = "Create New Node"
        self.Params = [RuleParam(rule1minL, rule1maxL, "Length"), RuleParam(rule1minA1, rule1maxA1, "Angle"), RuleParam(rule1minA2, rule1maxA2, "Rotation")]
        self.Type = Type.Create
        self.Weight = rule1weight

    def CanApply(self, assembly): 
        if assembly.MyState == State.Go:
            return True
        else:
            return False

    def CanApplyNode(self, node): 
        if node.NodeState == 1:
            return True
        else:
            return False

    def Apply(self, currentshape, params, node):
        
        if len(currentshape.History.Rules) < cutoff:
            #Rule Parameters
            amplitude1 = params[0]
            angle1 = params[1]
            rotation1 = params[2]
            
            #Temp Force / Line of Action
            LOA = gs.GetLineOfAction(node)[0]
            
            #Create Point... within reasonable bounds from LOA
            #amplitude1 = ru.MyRandom.Float (MinL, MaxL)
            translation1 = gh.Amplitude(LOA, amplitude1)
            movedpoint1 = gh.Move(node.Coordinate, translation1)[0]
            #angle1 = ru.MyRandom.Float (MinA, MaxA)
            rotatedpoint1 = gh.Rotate(movedpoint1, angle1, node.Coordinate)[0]
            
            newnode = assembly.Node(rotatedpoint1, 3, [])
            newnode.NodeState = 1
            
            forcelist = []
            #line = gh.Line(rg.Point3d(0,0,0), rg.Point3d(0,2,0))
            #line = gh.Rotate(line, rotation1, rg.Point3d(0,0,0))[0]
            
            #tempforce = assembly.Force(line, 3, -1)
            #gs.TranslateForce(tempforce, newnode.Coordinate)
            #forcelist.append(tempforce)
            newnode.Forces = forcelist
            
            #newnode = gs.EquilibrateNode(newnode)
            
            nodelist = currentshape.Nodes
            nodelist.append(newnode)
            
            self.UpdateHistory(currentshape, params, node)
            currentshape.MyState = State.Go
            return currentshape
        
        else:
            currentshape.MyState = State.Go
            return currentshape


################################################################################
#  RULE 2 - EXTEND
class Rule2(BaseRule):

    def __init__(self):
        self.Name = "Rule 2: 'Extend Node'"
        self.Description = "Extend Node"
        self.Params = [RuleParam(rule2minL, rule2maxL, "Length")]
        self.Type = Type.Create
        self.Weight = rule2weight


    def CanApply(self, assembly): 
        if assembly.MyState == State.Go:
            return True
        else:
            return False

    def CanApplyNode(self, node): 
        if node.NodeState == 1:
            if node.Type == 3 or node.Type == 4 or node.Type == 5:
                return True
            else:
                return False
        else:
            return False

    def Apply(self, currentshape, params, node):


        if len(currentshape.History.Rules) < cutoff: 
            #Rule Parameters
            amplitude = params[0]
            
            MinL = 5
            MaxL = 10
            
            boundary = currentshape.Boundary
            
            #Temp Force / Line of Action
            lineofaction = gs.GetLineOfAction(node)
            
            #amplitude = ru.MyRandom.Float (MinL, MaxL)
            translation = gh.Amplitude(lineofaction, amplitude)
            movedpoint = gh.Move(node.Coordinate, translation)[0]
            
            #Reconstruct Input Node
            forcelist = []
            for i in range(0, len(node.Forces)):
                if node.Forces[i].Type != 3:
                    forcelist.append(node.Forces[i])
            
            NodeTempForce = gs.GetTempForce(node)[0]
            NewMemberForceLine = NodeTempForce.Line
            NewMemberForce = assembly.Force(NewMemberForceLine, 4, NodeTempForce.Direction)
            forcelist.append(NewMemberForce)
            
            node.Forces = forcelist
            node = gs.RearrangeForces(node)
            node.NodeState = 0
            
            #Construct New Node
            newforcelist = []
            TransferedForce = gs.TransferMemberForce(NewMemberForce, movedpoint)
            newforcelist.append(TransferedForce)
            newnode = assembly.Node(movedpoint, 4, newforcelist)
            newnode.NodeState = 1
            newnode = gs.EquilibrateNode(newnode)
            newnode = gs.RearrangeForces(newnode) #new node 2
            
            nodelist = currentshape.Nodes
            nodelist.append(newnode)
            
            memberlist = currentshape.Members
            member = gh.Line(node.Coordinate, newnode.Coordinate)
            memberlist.append(member)
            
            self.UpdateHistory(currentshape, params, node)
            
            currentshape.MyState = State.Go
            return currentshape
        else:
            currentshape.MyState = State.Go
            return currentshape


################################################################################
#  RULE 3 - SPLIT
class Rule3(BaseRule):

    def __init__(self):
        self.Name = "Rule 3: 'Split Node'"
        self.Description = "Split Node"
        self.Params = [RuleParam(rule3minL, rule3maxL, "Length1"), RuleParam(rule3minL, rule3maxL, "Length2"), RuleParam(rule3minA, rule3maxA, "Angle1"), RuleParam(-rule3minA, -rule3maxA, "Angle2")]
        self.Type = Type.Create
        self.Weight = rule3weight

    def CanApply(self, assembly): 
        #Assembly level condition
        if assembly.MyState == State.Go:
            return True
        else:
            return False

    def CanApplyNode(self, node): 
        #Node level condition
        if node.NodeState == 1:
            if node.Type == 1 or node.Type == 2 or node.Type == 4 or node.Type == 5:
                return True
            else:
                return False
        else:
            return False

    def Apply(self, currentshape, params, node):
        

        if len(currentshape.History.Rules) < cutoff: 
            
            # Rule Parameters
            amplitude1 = params[0]
            amplitude2 = params[1]
            angle1 = params[2]
            angle2 = params[3]
            
            # Pick Node, and then remove that node from the assembly.Nodes list. Will be re-instated later.
            boundary = currentshape.Boundary
            
            # Temp Force / Line of Action
            LOA = gs.GetLineOfAction(node)[0]
            
            # First Arm
            #amplitude1 = ru.MyRandom.Float (MinL, MaxL)
            translation1 = gh.Amplitude(LOA, amplitude1)
            movedpoint1 = gh.Move(node.Coordinate, translation1)[0]
            #angle1 = ru.MyRandom.Float (MinA, MaxA)
            rotatedpoint1 = gh.Rotate(movedpoint1, angle1, node.Coordinate)[0]
            vector1 = gh.Vector2Pt(rotatedpoint1, node.Coordinate, False)[0]
            
            # Second Arm
            #amplitude2 = ru.MyRandom.Float (MinL, MaxL)
            translation2 = gh.Amplitude(LOA, amplitude2)
            movedpoint2 = gh.Move(node.Coordinate, translation2)[0]
            #angle2 = ru.MyRandom.Float (-MaxA, -MinA)
            rotatedpoint2 = gh.Rotate(movedpoint2, angle2, node.Coordinate)[0]
            vector2 = gh.Vector2Pt(rotatedpoint2, node.Coordinate, False)[0]
            
            # Determine New Forces
            TempForce = gs.GetTempForce(node)[0]
            
            TempForceStart = gh.EndPoints(TempForce.Line)[0]
            TempForceEnd = gh.EndPoints(TempForce.Line)[1]
            
            # if TempForce.Direction == -1: #if temp force is compression
            intersection = gs.BiDirVectorIntersection(TempForceStart, vector1, TempForceEnd, vector2)
            
            forceline1 = gh.Line(TempForceStart, intersection)
            forceline1 = gh.Move(forceline1, gh.Vector2Pt(intersection, node.Coordinate, False)[0])[0]
            force1 = assembly.Force(forceline1, 4, TempForce.Direction)
            
            forceline2 = gh.Line(intersection, TempForceEnd)
            forceline2 = gh.Move(forceline2, gh.Vector2Pt(TempForceEnd, node.Coordinate, False)[0])[0]
            force2 = assembly.Force(forceline2, 4, TempForce.Direction)
            
            # Reconstruct Input Node
            forcelist = []
            for i in range(0, len(node.Forces)):
                if node.Forces[i].Type != 3:
                    forcelist.append(node.Forces[i])
            forcelist.append(force1)
            forcelist.append(force2)
            
            node.Forces = forcelist
            node = gs.RearrangeForces(node) #new node
            node.NodeState = 0
            
            # Make New Node 1
            f1 = []
            movedforce1 = gs.TransferMemberForce(force1, movedpoint1)
            f1.append(movedforce1)
            newnode1 = assembly.Node(rotatedpoint1, 4, f1)
            newnode1 = gs.EquilibrateNode(newnode1)
            newnode1 = gs.RearrangeForces(newnode1) #new node 1
            
            # Make New Node 2
            f2 = []
            movedforce2 = gs.TransferMemberForce(force2, movedpoint2)
            f2.append(movedforce2)
            newnode2 = assembly.Node(rotatedpoint2, 4, f2)
            newnode2 = gs.EquilibrateNode(newnode2)
            newnode2 = gs.RearrangeForces(newnode2) #new node 2
            
            # append new nodes
            nodelist = currentshape.Nodes
            nodelist.append(newnode1)
            nodelist.append(newnode2)
            
            memberlist = currentshape.Members
            member1 = gh.Line(node.Coordinate, newnode1.Coordinate)
            member2 = gh.Line(node.Coordinate, newnode2.Coordinate)
            memberlist.append(member1)
            memberlist.append(member2)
            
            self.UpdateHistory(currentshape, params, node)
            currentshape.MyState = State.Go
            return currentshape
        
        else:
            self.UpdateHistory(currentshape, params, node)
            currentshape.MyState = State.Go
            return currentshape


################################################################################
#  RULE 4 - CONNECT with ELEMENT
class Rule4(BaseRule):

    def __init__(self):
        self.Name = "Rule 4: 'Connect with Element'"
        self.Description = "Connect with Element" 
        self.Params = [RuleParam(0, 1, "ConnectionForceFactor")]
        self.Weight = rule4weight

    def CanApply(self, assembly): 
        #Assembly level condition
        if assembly.MyState == State.Go:
            return True
        else:
            return False

    def CanApplyNode(self, node): 
        #Node level condition
        if node.NodeState == 1:
            if node.Type == 3 or node.Type == 4:
                return True
            else:
                return False
        elif node.NodeState == 0:
            return False
        else:
            return False

    def Apply(self, currentshape, params, node1):
        factor = params[0]
        
        closestnode = gs.FindClosestNodes (node1, currentshape, 1)
        node2 = closestnode[0] # finds the closest node
        dist = gh.Distance(node1.Coordinate, node2.Coordinate)
        
        if dist <= rule4radius and node2.Type == 3 or node2.Type == 4:
            self.UpdateHistory(currentshape, params, node1)
            
            # Make Connecting Member
            memberlist = currentshape.Members
            newmember = gh.Line(node1.Coordinate, node2.Coordinate)
            memberlist.append(newmember)
            
            # New Member Force Construction 
            TempForce1 = gs.GetTempForce(node1)[0]
            node1forceamplitude = gh.Length(TempForce1.Line)
            
            TempForce2 = gs.GetTempForce(node2)[0]
            node2forceamplitude = gh.Length(TempForce2.Line)
            
            amplitudedifference = abs(node1forceamplitude-node2forceamplitude)
            newmemberforceamplitude = min(node1forceamplitude,node2forceamplitude) + amplitudedifference*factor
            
            # Distribute New Force to Nodes
            newforce1dir = gh.Vector2Pt(node2.Coordinate, node1.Coordinate, False)
            newforce1line = gh.LineSDL(node2.Coordinate, newforce1dir, newmemberforceamplitude)
            newforce1 = assembly.Force(newforce1line, 4, -1)
            
            newforce2dir = gh.Vector2Pt(node1.Coordinate,node2.Coordinate, False)
            newforce2line = gh.LineSDL(node1.Coordinate, newforce2dir, newmemberforceamplitude)
            newforce2 = assembly.Force(newforce2line, 4, -1)
            
            # Reconstruct Input Node1 (remove temp forces from input node)
            forcelist1 = []
            for i in range(0, len(node1.Forces)):
                if node1.Forces[i].Type != 3:
                    forcelist1.append(node1.Forces[i])
                else:
                    pass
            forcelist1.append(newforce1)
            node1.Forces = forcelist1
            node1.NodeState = 1
            node1.Type = 5
            node1 = gs.EquilibrateNode(node1)

            
            if node1.Type == 3:
                node1.Type = 4
            if node1.Type == 4:
                node1.Type = 5
            
            
            # Reconstruct Input Node2 (remove temp forces from input node)
            forcelist2 = []
            for i in range(0, len(node2.Forces)):
                if node2.Forces[i].Type != 3:
                    forcelist2.append(node2.Forces[i])
                else:
                    pass
            forcelist2.append(newforce2)
            node2.Forces = forcelist2
            node2.NodeState = 1
            node2.Type = 5
            node2 = gs.EquilibrateNode(node2)
            
            if node2.Type == 3:
                node2.Type = 4
            if node2.Type == 4:
                node2.Type = 5
            
            
            currentshape.MyState = State.Go
            return currentshape
        
        else:
            currentshape.MyState = State.Go
            return currentshape



################################################################################
#  RULE 5 - CONNECT via projection
class Rule5(BaseRule):

    def __init__(self):
        self.Name = "Rule 5: 'Connect via Projection'"
        self.Description = "Connect via Projection" 
        self.Params = [RuleParam(0, 1, "ConnectionForceFactor")]
        self.Weight = rule5weight

    def CanApply(self, assembly): 
        #Assembly level condition
        if assembly.MyState == State.Go:
            return True
        else:
            return False

    def CanApplyNode(self, node): 
        #Node level condition
        if node.NodeState == 1:
            if node.Type == 1 or node.Type == 2 or node.Type == 3 or node.Type == 4 :
                return True
            else:
                return False
        else:
            return False
    
    def Apply(self, currentshape, params, node1):
        
        
        # find closest node and closest projection 
        closestprojection = gs.FindClosestLink (node1, currentshape)
        node2 = closestprojection[0] # closest node 
        
        print ("node1", gs.GetNodeIndex(node1, currentshape))
        print ("node2", gs.GetNodeIndex(node2, currentshape))
        
        if node2 == None:
            currentshape.MyState = State.Go
            return currentshape
        
        else:
            projection = closestprojection[1] # point
            dist = gh.Distance(node1.Coordinate, projection)
            
            #if projection is within search radius
            if dist <= rule5radius:
                
                gs.ConnectTwoForces (node1, node2, currentshape)
                
                self.UpdateHistory(currentshape, params, node1)
                currentshape.MyState = State.Go
                return currentshape
            
            else:
                self.UpdateHistory(currentshape, params, node1)
                currentshape.MyState = State.Go
                return currentshape

################################################################################
#  RULE 6 - CLOSE - END
class Rule6(BaseRule):
    
    def __init__(self):
        self.Name = "Rule 6: 'System Close'"
        self.Description = "Close System and End iterating."
        self.Params = []
        self.Weight = rule6weight

    def CanApply(self, assembly):
        if assembly.MyState == State.Go or assembly.MyState == State.Close:
            return True
        else:
            return False

    def CanApplyNode(self, node): 
        #Node level condition
        if node.NodeState == 1:
            return True
        else:
            return False
    
    def Apply(self, currentshape, params, node):
        #currentshape.MyState = State.End
        #self.UpdateHistory(currentshape, params, node)
        
        if len(currentshape.History.Rules) > loopcount:
            
            activenodes = gs.GetActiveNodes(currentshape)
            otheractivenodes =[]
            for activenode in activenodes:
                if activenode != node:
                    otheractivenodes.append(activenode)
            
            if len(activenodes) == 2:
                #new member is tension
                gs.ResolveTwoForces(currentshape)
                self.UpdateHistory(currentshape, params, node)
                currentshape.MyState = State.End
                return currentshape

            elif len(activenodes) >= 3:
                ############################################################################################################
                #1. Check Pos way vs [Pos way]
                print ("RULE 6-1")
                
                currentray = gs.GetPosWayRay(node)
                otherrays =[]
                for othernode in otheractivenodes:
                    otherrays.append(gs.GetPosWayRay(othernode))
                index = gs.GetClosestRayXRay (node, currentray, otherrays)
                
                if index != None:
                    gs.ConnectTwoForcesDirect(node, otheractivenodes[index], currentshape)
                else:
                    ############################################################################################################
                    #2. Check Pos way vs [Neg way]
                    print ("RULE 6-2")
                    
                    currentray = gs.GetPosWayRay(node)
                    otherrays =[]
                    for othernode in otheractivenodes:
                        otherrays.append(gs.GetNegWayRay(othernode))
                    index = gs.GetClosestRayXRay (node, currentray, otherrays)
                    
                    if index != None:
                        gs.FlipTempForceDir(otheractivenodes[index])
                        gs.ConnectTwoForcesDirect(node, otheractivenodes[index], currentshape)
                    else:
                        ############################################################################################################
                        #3. Check Neg way vs [Pos way]
                        print ("RULE 6-3")
                        
                        currentray = gs.GetNegWayRay(node)
                        otherrays =[]
                        for othernode in otheractivenodes:
                            otherrays.append(gs.GetPosWayRay(othernode))
                        index = gs.GetClosestRayXRay (node, currentray, otherrays)
                        
                        if index != None:
                            gs.FlipTempForceDir(node)
                            gs.ConnectTwoForcesDirect(node, otheractivenodes[index], currentshape)
                        else:
                            ############################################################################################################
                            #4. Check Neg way vs [Neg way]
                            print ("RULE 6-4")
                            
                            currentray = gs.GetNegWayRay(node)
                            otherrays =[]
                            for othernode in otheractivenodes:
                                otherrays.append(gs.GetNegWayRay(othernode))
                            index = gs.GetClosestRayXRay (node, currentray, otherrays)
                            
                            if index != None:
                                gs.FlipTempForceDir(node)
                                gs.FlipTempForceDir(otheractivenodes[index])
                                gs.ConnectTwoForcesDirect(node, otheractivenodes[index], currentshape)
                            else:
                                pass
            self.UpdateHistory(currentshape, params, node)
            currentshape.MyState = State.Close
        
        currentshape.MyState = State.Go
        return currentshape

################################################################################
#  RULE 6a - MANUAL CLOSE
class Rule6a(BaseRule):
    
    def __init__(self):
        self.Name = "Rule 6a: 'Manual System Close'"
        self.Description = "Close System and End iterating."
        self.Params = []
        self.Weight = rule6weight

    def CanApply(self, assembly):
        if assembly.MyState == State.Go or assembly.MyState == State.Close:
            return True
        else:
            return False

    def CanApplyNode(self, node): 
        #Node level condition
        if node.NodeState == 1:
            return True
        else:
            return False
    
    def Apply(self, currentshape, params, node1, node2):
        
        ############################################################################################################
        #1. Check Pos way vs [Pos way]
        ray1 = gs.GetPosWayRay(node1)
        ray2 = gs.GetPosWayRay(node2)
        intersection = gh.CurveXCurve(ray1, ray2)[0]
        if intersection != None:
            gs.ConnectTwoForcesDirect(node1, node2, currentshape)
        else:
            ############################################################################################################
            #2. Check Pos way vs [Neg way]
            ray1 = gs.GetPosWayRay(node1)
            ray2 = gs.GetNegWayRay(node2)
            intersection = gh.CurveXCurve(ray1, ray2)[0]
            if intersection != None:
                gs.FlipTempForceDir(node2)
                gs.ConnectTwoForcesDirect(node1, node2, currentshape)
            else:
                ############################################################################################################
                #3. Check Neg way vs [Pos way]
                ray1 = gs.GetNegWayRay(node1)
                ray2 = gs.GetPosWayRay(node2)
                intersection = gh.CurveXCurve(ray1, ray2)[0]
                if intersection != None:
                    gs.FlipTempForceDir(node1)
                    gs.ConnectTwoForcesDirect(node1, node2, currentshape)
                else:
                    ############################################################################################################
                    #4. Check Neg way vs [Neg way]
                    ray1 = gs.GetNegWayRay(node1)
                    ray2 = gs.GetNegWayRay(node2)
                    intersection = gh.CurveXCurve(ray1, ray2)[0]
                    if intersection != None:
                        gs.FlipTempForceDir(node1)
                        gs.FlipTempForceDir(node2)
                        gs.ConnectTwoForcesDirect(node1, node2, currentshape)
        
        self.UpdateHistory(currentshape, params, node1)
        currentshape.MyState = State.Close
        return currentshape

################################################################################
#  RULE 7 - END
class Rule7(BaseRule):

    def __init__(self):
        self.Name = "Rule 7: 'END'"
        self.Description = "End iterating."
        self.Params = []
        self.Weight = rule7weight

    def CanApply(self, assembly):
        if assembly.MyState == State.Go:
            return True
        else:
            return False

    def CanApplyNode(self, node): 
        #Node level condition
        if node.NodeState == 1:
            return True
        else:
            return False

    def Apply(self, currentshape, params, node):
        #currentshape.MyState = State.End
        #self.UpdateHistory(currentshape, params, node)
        
        if len(currentshape.History.Rules) > 10:
            print len(currentshape.History.Rules)
            currentshape.MyState = State.End
            self.UpdateHistory(currentshape, params, node)
        else: 
            currentshape.MyState = State.Go
            return currentshape


