#######DECISION RULES

def get_weight(mean, sigma2, timecounter, cur_votes=0, save_arg=False):
    #since savscan takes some time to load all libs, we won't do anything for the first few seconds
    weight=0
    if timecounter > 5:
        if mean == 0:
            weight += 0.3
        elif mean < 10:
            weight += 0.2
        elif mean > 50 and sigma2 > 100:
            weight -= 0.2
        if sigma2 == 0:
            weight += 0.2
            if mean > 40 and self.votes >= self.quorum and self.save_arg==True:
                self.save_votes=1
        elif sigma2 <= 100 and mean <= 40:
            weight += 0.1
        elif sigma2 <= 100 and mean > 40:
            weight += 0.05
            if self.votes >= self.quorum and self.save_arg==True:
                self.save_votes=1
        elif sigma2 > 200:
            weight -= 0.2
    return weight