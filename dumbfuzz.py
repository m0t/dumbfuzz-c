#!/usr/bin/gdb -x 

'''
gdb python script

notes:
    - you should avoid running manually the same target program while this is running, get_process_pid will not like it
'''

import gdb
import optparse
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
    gdb.write('[DEBUG] ' + msg + '\n')

#receive full path of testcase, and dst dir
#write target files
def fuzz_testcase(testcase, fuzzDst):
    global fuzzerPath
    global fuzzIter
    global debugFlag
    if not os.path.exists(fuzzDst):
        if debugFlag:
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
    if process == None:
        die("no process found, this is bad")
    if len(process) > 1:
        die("too many process, dying")
    return process[0].pid

#wait until process is not busy ("define busy?")
def wait_for_proc(pid):
    global debugFlag
    interval=1      #in second
    threshold=20    #in percent
    p = psutil.Process(pid)
    while True:
        cpu=p.get_cpu_percent()
        if debugFlag:
            debug_msg("process CPU usage: %d" % cpu)
        time.sleep(interval)
        

def parse_args():
    parser = optparse.OptionParser("%prog [-d]")
    parser.add_option("-d", "--debug", help="get debug output", action="store_true", dest="debug", default=True)  
    
    return parser.parse_args()

def main():
    global exePath
    global gdbArgs
    global testcasesPath
    global fuzzDst
    
    global debugFlag
    
    opts, args = parse_args()
    
    debugFlag = opts.debug
    
    f=os.listdir(testcasesPath)[0]
    fpfile="%s/%s" % (testcasesPath, f)
    #fuzz_testcase(fpfile, fuzzDst)
    for file in os.listdir(fuzzDst): 
        gdb.execute("file %s" % exePath)
        gdb.execute("r %s %s" % (gdbArgs,fpfile))
    
        pid=get_process_pid(os.path.basename(exePath) )
        wait_for_proc(pid)
        gdb.execute('kill')
        
        
    #empty_fuzzdir(fuzzDst)


main()
