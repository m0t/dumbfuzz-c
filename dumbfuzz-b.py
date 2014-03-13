#!/usr/bin/python3

'''
gdb python script

notes:
    - you should avoid running manually the same target program while this is running, get_process_pid will not like it
'''

import optparse
import threading
import psutil
import time
import os
import sys

####GLOBAL###
exePath="/usr/lib/libreoffice/program/soffice.bin"
gdbArgs='--impress'
testcasesPath="/mnt/shared/ppt"
crashesPath=""
logsPath=""
fuzzerPath="./radamsa-bin"
fuzzIter=200
fuzzDst="fuzzed"
restoreFlag = False
debugFlag = False

#############

"""
for every file
fuzz it
iterate fuzzed
check for crashes
close program if nothing happens
"""

def die(msg):
    sys.stderr.write("[ERROR] " + msg + "\n")
    sys.exit(-1)

def debug_msg(msg):
    global debugFlag
    if debugFlag:
        sys.stdout.write('[DEBUG] ' + msg + '\n')
    return

#receive full path of testcase, and dst dir
#write target files
def fuzz_testcase(testcase, fuzzDst):
    global fuzzerPath
    global fuzzIter
    if not os.path.exists(fuzzDst):
        debug_msg("creating dir %s\n" % (fuzzDst))
        os.mkdir(fuzzDst)
    if debugFlag:
        fuzzCmd = "%s -v -n %d -o %s/fuzzed-%%n.ppt %s" % (fuzzerPath, fuzzIter, fuzzDst, testcase)
        debug_msg(fuzzCmd)
    else:
        fuzzCmd = "%s -n %d -o %s/fuzzed-%%n.ppt %s" % (fuzzerPath, fuzzIter, fuzzDst, testcase)
    ret = os.system(fuzzCmd)
    if (ret != 0):
        die("fuzzer failed to run")
    return

def empty_fuzzdir(fuzzDst):
    os.system("rm -rf %s/*" % fuzzDst)

#we should do this with gdb, idiot
def get_process_pid(pname):

    process = list(filter(lambda p: p.name == pname, psutil.process_iter()))
    #there should be one and only one, check this
    if len(process) == 0:
        debug_msg("no process found, this is bad")
        return None
    if len(process) > 1:
        die("too many process, dying")
    return process[0].pid

def getSigma2(l, mean):
    s2=[]
    for i in l:
        s2 += i*i
    return (sum(s2)/len(s2))-(mean*mean)

#wait until process is not busy ("define busy?")
#XXX blocking?
def wait_for_proc(pid):
    global debugFlag
    interval=1      #in second
    nslices=5
    threshold=20    #in percent
    p = psutil.Process(pid)
    while True:
        cpu=[]
        for i in range(0,nslices):
            cpu += p.get_cpu_percent()
            time.sleep(interval/slices)
        mean=sum(cpu)/len(cpu)
        sigma2=get_sigma2(cpu, mean)
        debug_msg("avg process CPU usage: %d" % mean)
        debug_msg("variance is: %d" % sigma2)

#run in a separate thread, wait for process to load, kill it when it stop loading
#XXX blocking?
def proc_checker():
    global exePath
    
    while True:        
        pid=get_process_pid(os.path.basename(exePath) )
        if pid:
            break
        time.sleep(0.2)
    wait_for_proc(pid)
    

def parse_args():
    parser = optparse.OptionParser("%prog [-d]")
    parser.add_option("-d", "--debug", help="get debug output", action="store_true", dest="debug", default=True)  
    
    return parser.parse_args()

def main():
    global exePath
    global gdbArgs
    global testcasesPath
    global fuzzDst
    
    opts, args = parse_args()
    
    debugFlag = opts.debug
    
    f=os.listdir(testcasesPath)[0]
    fpfile="%s/%s" % (testcasesPath, f)
    #fuzz_testcase(fpfile, fuzzDst)
    #for file in os.listdir(fuzzDst):
        #gdb.execute("file %s" % exePath)
    debug_msg("start checker thread")
    threading.Thread(target=proc_checker).start()
    debug_msg("run target")
    os.system("./launcher.py %s" % exePath)
          
    #empty_fuzzdir(fuzzDst)


main()
