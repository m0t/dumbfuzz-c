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
    sys.stderr.write("MONITOR ERROR" + msg + "\n")
    sys.exit(-1)
