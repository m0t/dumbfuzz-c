class Decider(object):
    quorum=1
    save_quorum=1
    rules_file='decision_rules.py'    
    
    def __init__(self,save_arg=False):
        self.votes=0
        self.save_votes=0
        self.save_arg=save_arg
        self.weight=0
        
    def update(self, mean, sigma2, timecounter):
        #init votes to 0
        if self.votes < 0:
            self.votes = 0
        
        weight=self.weight
        
        #run decision rules, all vars should be already declared at this point
        code=compile(open(self.rules_file).read(),'<string>','exec')
        exec(code)
        
        self.weight=weight
        self.votes += self.weight
        return True
        
    def isQuorumReached(self):
        if self.votes >= self.quorum:
            return True
        return False
            
    def isSaveQuorumReached(self):
        if self.save_votes >= self.save_quorum:
            return True
        return False