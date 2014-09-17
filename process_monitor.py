#!/usr/bin/python3

from procmon import *

def check_psutil():
    if psutil.version_info[0] == 2:
        return True
    return False

def main():
    
    #checker_thread=threading.Thread(target=proc_checker, args=[proc_dead])
    #checker_thread.start()
    if len(sys.argv) != 3:
        die("%s <executable> <searchargs>" % sys.argv[0])
    
    if not check_psutil():
        die("need psutil >= 2.0")
        
    exeFile=sys.argv[1]
    exeArgs=sys.argv[2]
    
    try:
        procmon=ProcMon(exeFile,exeArgs)
        procmon.start()
    except KeyboardInterrupt:
        #XXX pretty useless
        debug_msg("ctrl-c detected, killing")
        procmon.cleanup_and_exit(-1)
   
main()