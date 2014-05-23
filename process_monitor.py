#!/usr/bin/python3

import threading
import psutil
import time
import os
import shutil
import sys

from procmon import *


debugFlag=True
processTimeout=20 #seconds
savedir="saved" #where to save testcase if interesting but not catched by debugger
pipename="/tmp/monitor_pipe0"

def debug_msg(msg):
    global debugFlag
    if debugFlag:
        #well, really a best effort thing
        try:
            sys.stdout.write('[MONITOR] ' + msg + '\n')
        except:
            pass 
    return
    
def die(msg):
    sys.stderr.write("MONITOR ERROR" + msg + "\n")
    sys.exit(-1)


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
    
    procmon=ProcMon(exeFile,exeArgs)
    procmon.start()

main()