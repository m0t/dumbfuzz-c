#######DECISION RULES
#available args mean, sigma2, timecounter

#since savscan takes some time to load all libs, we won't do anything for the first few seconds
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
        if votes >= self.quorum and self.save_arg==True:
            self.save_votes=1
    elif sigma2 > 200:
        weight -= 0.2
#########END OF RULES