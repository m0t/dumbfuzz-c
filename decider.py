class Decider(Object):
    quorum=1
    save_quorum=1    
    
    def __init__(self,save_arg=False):
        self.votes=0
        self.save_votes=0
        self.save_arg=save_arg
        
    def update(mean, sigma2, timecounter):
        #init votes to 0
        if self.votes < 0:
            self.votes = 0
        
        weight=0
        
        #run decision rules, all vars should be already declared at this point
        from decision_rules import *    

        self.votes += weight
        return True
        
    def isQuorumReached():
        if self.votes >= self.quorum:
            return True
        return False
            
    def isSaveQuorumReached():
        if self.save_votes >= self.save_quorum:
            return True
        return False