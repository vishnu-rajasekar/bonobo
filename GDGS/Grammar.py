import Assembly as assembly
import RandomUtility as ru
import Rules as rules
import ghpythonlib.components as gh
import Rhino.Geometry as rg


import GraphicStatics as gs

################################################################################

reload (assembly)
reload (gs)


class Grammar:

    def __init__(self):
        self.MyRules = []
        self.LoadRules()
        self.SetRuleGrammar()
        #self.Assembly = assembly

    def LoadRules(self): 
        # STEP 1 : compile all rules into one list = MyRules
        self.MyRules.append(rules.Rule0())
        #self.MyRules.append(rules.Rule1())
        self.MyRules.append(rules.Rule2())
        self.MyRules.append(rules.Rule3())
        self.MyRules.append(rules.Rule4())
        self.MyRules.append(rules.Rule5())
        self.MyRules.append(rules.Rule6())
        #self.MyRules.append(rules.Rule6a())
        self.MyRules.append(rules.Rule7())

    def SetRuleGrammar(self): 
        for r in self.MyRules:
            r.MyGrammar = self

    def GetAllRules(self): 
        # STEP 2 : recompile rules based on weight... 5 means append it 5 times
        weightedRules = []
        for r in self.MyRules:
            if r.Weight > 0:
                for i in range(r.Weight):
                    weightedRules.append(r)
        return weightedRules

    def GetPossibleRules(self, thisAssembly): 
        # STEP 3 : recompile rules base on whether its applicability
        possibleRules = []
        allRules = self.GetAllRules()
        for r in allRules:
            if r.CanApply(thisAssembly): #boolean, defined in each rule
                possibleRules.append(r) #if True, append
        return possibleRules

    def GetPossibleNodeRules(self, thisAssembly, thisNode): 
        # STEP 4 : recompile rules base on whether its applicability
        possibleNodeRules = []
        allNodeRules = self.GetAllRules()
        for r in allNodeRules:
            if r.CanApply(thisAssembly) and r.CanApplyNode(thisNode): #boolean, defined in each rule
                possibleNodeRules.append(r) #if True, append
        return possibleNodeRules


class RandomComputation:

    def __init__(self, grammar): 
        #takes in grammar class as input
        self.MyGrammar = grammar
        #self.Assembly = currentshape

    def GenerateRandomAssembly(self, currentshape):
        while currentshape.MyState != rules.State.End: #if not end state, proceed to ApplyRandomRule
            currentshape = self.ApplyRandomRule(currentshape)
        
        #currentshape.Score = currentshape.GetScore()
        #currentshape.Length = currentshape.GetLength()
        return currentshape

    def ApplyRandomRule(self, currentshape): 
        node = currentshape.RandomNodePicker() # PICK RANDOM NODE
        
        if len(currentshape.History.Rules) > 20:
            pass
            #currentshape.MyState = 4
        else:
            rules = self.MyGrammar.GetPossibleNodeRules(currentshape, node)# GATHER APPLICABLE RULES FOR THE SELECTED NODE
            rulecount = len(rules)
            if rulecount > 0:
                index = ru.MyRandom.Btwn(0, rulecount - 1) #Random integer, generated from RandomUtility
                rule = rules[index]
                params = self.GenerateRandomParams(rule)
                currentshape = rule.Apply(currentshape, params, node)
                print ("********************NEW RULE APPLIED", rule.Name,  "at picked node", gs.GetNodeIndex(node, currentshape))
                return currentshape
    
            else:
                return currentshape
            
            
    def SelectRandomRule(self, currentshape): 
        node = currentshape.RandomNodePicker() # PICK RANDOM NODE
        
        if len(currentshape.History.Rules) > 20:
            pass
            #currentshape.MyState = 4
        else:
            rules = self.MyGrammar.GetPossibleNodeRules(currentshape, node)# GATHER APPLICABLE RULES FOR THE SELECTED NODE
            rulecount = len(rules)
            if rulecount > 0:
                index = ru.MyRandom.Btwn(0, rulecount - 1) #Random integer, generated from RandomUtility
                rule = rules[index]
                params = self.GenerateRandomParams(rule)
                nodeindex = gs.GetNodeIndex(node, currentshape)
                selectedrule = [rule, params, nodeindex]

                print ("********************NEW RULE SELECTED", rule.Name,  "at picked node", gs.GetNodeIndex(node, currentshape))
                return selectedrule

            else:
                pass
            
    """ def ApplyRule(self, currentshape, selrule):
         
         currentshape = selrule[0].Apply(currentshape, selrule[1], currentshape.Nodes[selrule[2]])
         return currentshape """
    
    def ApplyRule(self, currentshape, selrule):
         
        currentshape = selrule[0].Apply(currentshape, selrule[1], currentshape.Nodes[selrule[2]])
        return currentshape
    

    def GenerateRandomParams(self, rule):
        num = len(rule.Params)
        p = []
        for i in range(num):
            paramValue = rule.Params[i].GetRandomValue()

            p.append(paramValue)
        return p