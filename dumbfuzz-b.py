#!/usr/bin/python3

'''
gdb python script

notes:
    - you should avoid running manually the same target program while this is running, get_process_pid will not like it
'''

import subprocess
import optparse
import threading
import psutil
import time
import os
import sys

####GLOBAL###
exePath="/usr/lib/libreoffice/program/soffice.bin"
gdbArgs='--impress'
#testcasesPath="/mnt/shared/ppt"
crashesPath=""
logsPath=""
fuzzerPath="./radamsa-bin"
fuzzIter=200
fuzzDst="fuzzed"
restoreFlag = False
debugFlag = True
processTimeout=20 #seconds
listfile='filelist.txt'


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

'''
#we should do this with gdb, idiot
def get_process_pid(pname):

    process = list(filter(lambda p: p.name == pname, psutil.process_iter()))
    #there should be one and only one, check this
    if len(process) == 0:
        debug_msg("no process found")
        return None
    if len(process) > 1:
        die("too many process, dying")
    return process[0].pid

def getSigma2(l, mean):
    s2=[]
    for i in l:
        s2.append(i*i)
    return (sum(s2)/len(s2))-(mean*mean)

#wait until process is not busy ("define busy?")
#XXX blocking?
#things: set timeout, some files can really take time, save long running files in case, 
def wait_for_proc(pid, timeout):
    global debugFlag
    interval=1.0      #in second
    nslices=5
    threshold=20    #in percent
    p = psutil.Process(pid)
    while not timeout.is_set():
        cpu=[]
        for i in range(0,nslices):
            cpu.append(p.get_cpu_percent())
            time.sleep(interval/nslices)
        mean=sum(cpu)/len(cpu)
        sigma2=getSigma2(cpu, mean)
        debug_msg("avg process CPU usage: %d" % mean)
        debug_msg("variance is: %d" % sigma2)
    
    debug_msg("timeout reached, killing the process and dying")
    p.kill()

#run in a separate thread, wait for process to load, kill it when it stop loading
#XXX blocking?
def proc_checker():
    global exePath
    
    while True:        
        pid=get_process_pid(os.path.basename(exePath) )
        if pid:
            debug_msg("pid found: %d ; starting timer thread" % pid)
            timeout=threading.Event()
            threading.Thread(target=timer_thread, args=[timeout]).start()
            break
        time.sleep(0.2)
    wait_for_proc(pid,timeout)
    

def timer_thread(event):
    global processTimeout
    time.sleep(processTimeout)
    event.set()
'''

def parse_args():
    parser = optparse.OptionParser("%prog [some opts] [-L filelist]|[-D fuzzdir]")
    parser.add_option("-v", "--debug", help="get debug output", action="store_true", dest="debug", default=True)
    parser.add_option("-s", "--export", help="save filelist.txt ", action="store_true", dest="saveList", default=False)
    parser.add_option("-S", "--skipto", help="skip to #n iteration", dest="skipto", default=None)
    parser.add_option("-L", "--list", help="read filelist from file", dest="filelist", default=None)
    parser.add_option("-D", "--fuzzdir", help="create filelist from dir", dest="fuzzdir", default=None)
    
    return parser.parse_args()

def main():
    global exePath
    global gdbArgs
    global testcasesPath
    global fuzzDst
    global debugFlag
    global listfile
    
    opts, args = parse_args()
    
    debugFlag = opts.debug
    
    if opts.filelist and opts.fuzzdir:
        die("options -L and -D are mutually exclusive")
    if not opts.filelist and not opts.fuzzdir:
        die("dickhead")
    if opts.fuzzdir:
        testcasesPath=opts.fuzzdir
        filelist=os.listdir(testcasesPath)
    if opts.filelist:
        if opts.saveList:
            debug_msg("already loading from filelist, unsetting writing")
            opts.saveList = False
        try:
            lf=open(opts.saveList)
            filelist=lf.read().split('\n')
        except:
            die('Impossible to load file list, check file and syntax')
    
    if not filelist:
        die("no input files were specified")
    
    if opts.saveList:
        debug_msg("saving list of files to %s" % listfile)
        lf = open(listfile)
        lf.write("\n".join([str(i) for i in filelist]))
        lf.close()
    
    #XXX: why is this try here?
    try:
        #XXX skipto
        f=filelist[0]
        fpfile="%s/%s" % (testcasesPath, f)
        #XXX debug_msg('fuzzing file #%d' % 0)
        debug_msg('bypassing all filelist conf while testing :)')
        #fuzz_testcase(fpfile, fuzzDst)
        #for file in os.listdir(fuzzDst):
            #gdb.execute("file %s" % exePath)
        #debug_msg("starting checker thread")
        #checker_thread=threading.Thread(target=proc_checker)
        #checker_thread.start()
        debug_msg("run target")
        gdb_proc = subprocess.Popen("./launcher.py --batch %s &" % "../gdb/a.out", shell="/usr/bin/python")
        #XXX: wait for gdb to return  
        #empty_fuzzdir(fuzzDst)
        gdb_proc.wait() 
    except KeyboardInterrupt:
        #close threads?
        debug_msg("Ctrl-c detected, exiting")
        gdb_proc.kill()
        sys.exit(0)


main()
