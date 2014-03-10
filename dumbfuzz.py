#!/usr/bin/gdb -x 
import gdb
import os

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
    if not os.path.exist(fuzzDst):
        os.mkdir(fuzzDst)
    ret = os.system("%s -n %d -o %s/fuzzed-%%n.ppt %s" % (fuzzerPath, fuzzIter, fuzzDst, testcase))
    if (ret != 0):
        die("fuzzer failed to run")
    return
    

def main():
    global exePath
    global gdbArgs
    global testcasesPath
    global fuzzDst
    #for each file in os.listdir(testcasesPath)
    f=os.listdir(testcasesPath)[0]
    fpfile="%s/%s" % (testcasesPath, f)
    #gdb.execute("file %s" % exePath)
    #gdb.execute("r %s %s" % (gdbArgs,fpfile))

def __main__():
    main()
