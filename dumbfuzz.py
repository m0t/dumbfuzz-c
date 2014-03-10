#!/usr/bin/gdb -x 

'''
gdb python script

notes:
    - you should avoid running manually the same target program while this is running, get_process_pid will not like it
'''

import gdb
import psutil
import optparse
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
    sys.stderr.write(msg + "\n")
    sys.exit(-1)

#receive full path of testcase, and dst dir
#write target files
def fuzz_testcase(testcase, fuzzDst):
    global fuzzerPath
    global fuzzIter
    global debugFlag
    if not os.path.exists(fuzzDst):
        if debugFlag:
            gdb.write("creating dir %s\n" % (fuzzDst))
        os.mkdir(fuzzDst)
    if debugFlag:
        fuzzCmd = "%s -v -n %d -o %s/fuzzed-%%n.ppt %s" % (fuzzerPath, fuzzIter, fuzzDst, testcase)
        gdb.write(fuzzCmd)
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
    process = filter(lambda p: p.name == pname, psutil.process_iter())
    #there should be one and only one, check this
    if process = None:
        die("no process found, this is bad")

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
    for each file in os.listdir(fuzzDst): 
        gdb.execute("file %s" % exePath)
        gdb.execute("r %s %s" % (gdbArgs,fpfile))
    
        pid=get_process_pid(os.path.basename(exePath) )
        
        
    #empty_fuzzdir(fuzzDst)


main()
