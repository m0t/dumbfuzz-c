#######DECISION RULES
def get_weight(mean, sigma2, timecounter, cur_votes=0, quorum=1, save_arg=False):
    weight=0
    #give it a second will you
    if timecounter > 3:
        
        if mean == 0:
            weight += 0.3
        elif mean < 10:
            weight += 0.2
        elif mean > 50 and sigma2 > 100:
            weight -= 0.2
        if sigma2 == 0:
            weight += 0.2
            if mean > 40 and cur_votes >= quorum and save_arg==True:
                #XXX save_votes needs fix
                weight=1
        elif sigma2 <= 100 and mean <= 40:
            weight += 0.1
        elif sigma2 <= 100 and mean > 40:
            weight += 0.05
            if cur_votes >= quorum and save_arg==True:
                weight=1
        elif sigma2 > 200:
            weight -= 0.2
    
    return weight
