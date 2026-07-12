import random

class RandomUtility:
    def __init__(self, s):
        random.seed(s)
        
    def Btwn(self, lb, ub):
        return random.randint(lb, ub)
        
    def Float(self, lb, ub):
        return random.uniform(lb, ub)


MyRandom = RandomUtility(1)