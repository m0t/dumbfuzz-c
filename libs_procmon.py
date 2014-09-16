import sys

def debug_msg(msg):
    #global debugFlag
    #if debugFlag:
        #well, really a best effort thing
    try:
        sys.stdout.write('[MONITOR] ' + msg + '\n')
    except:
        pass 
    return
    
def die(msg):
    sys.stderr.write("[ MONITOR ERROR ] " + msg + "\n")
    sys.exit(-1)

def getSigma2(self, l, mean):
    s2=[]
    for i in l:
        s2.append(i*i)
    return (sum(s2)/len(s2))-(mean*mean)