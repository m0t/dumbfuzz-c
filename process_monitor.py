#!/usr/bin/python3

import threading
import psutil
import time
import os
import shutil
import sys

from decider import *

debugFlag=True
processTimeout=20 #seconds
savedir="saved" #where to save testcase if interesting but not catched by debugger

def die(msg):
    sys.stderr.write("MONITOR ERROR" + msg + "\n")
    sys.exit(-1)

def timer_thread(event):
    global processTimeout
    time.sleep(processTimeout)
    event.set()

def getSigma2(l, mean):
    s2=[]
    for i in l:
        s2.append(i*i)
    return (sum(s2)/len(s2))-(mean*mean)

def debug_msg(msg):
    global debugFlag
    if debugFlag:
        #well, really a best effort thing
        try:
            sys.stdout.write('[MONITOR] ' + msg + '\n')
        except:
            pass 
    return

#search the file in the name, then search other args in the cmdline
def find_proc(file, args):
    pids=[]
    for proc in psutil.process_iter():
        if any(file in s for s in proc.cmdline()): #and not any(sys.argv[0] in s for s in proc.cmdline())
            if file.find(proc.name()) > 0:
                if any(args in s for s in proc.cmdline()):
                    debug_msg("process pid is "+str(proc.pid))
                    pids.append(proc.pid)
    if len(pids) == 0:
        return None
    return pids

#immediately kill and exit
def kill_proc_and_exit(p):
    p.kill()
    debug_msg("exiting")
    sys.exit(0)

def check_dir(dir):
    if not os.path.exists(dir):
        debug_msg("saved dir not found, creating")
        try:
            os.mkdir(dir)
        except PermissionError:
            debug_msg("saved dir creation failed, dying")
            sys.exit(-1)

def save_testcase(casefile):
    global savedir
    check_dir(savedir)
    strtime=time.strftime('%d-%m-%y_%H%M')
    if os.path.isdir(casefile):
        savefile="fuzzedcases-"+strtime
        debug_msg('passed whole testcases folder, copying everything ')
        shutil.copytree(casefile, savedir+savefile)
    else:
        savefile="fuzzedcase-"+strtime
        debug_msg('Saving testcase to ' + savefile)
        shutil.copy(casefile, savedir+savefile)

#wait until process is not busy ("define busy?")
#XXX blocking?
#things: set timeout, some files can really take time, save long running files in case,
#if proc_arg is provided, will save that file is deemed necessary
def wait_for_proc(pid, timeout, proc_arg=None):
    global debugFlag
    
    save_arg=False
    if proc_arg:
        save_arg=True
    
    '''
    XXX remove from here
    save_votes=0
    save_quorum=1
    votes=0
    quorum=1
    '''
    
    interval=1.0      #in second
    nslices=5
    
    decider = Decider(save_arg)
    
    p = psutil.Process(pid)
    timecounter = 0
    while not timeout.is_set():
        try:
            
            cpu=[]
            for i in range(0,nslices):
                cpu.append(p.get_cpu_percent())
                time.sleep(interval/nslices)
            mean=sum(cpu)/len(cpu)
            sigma2=getSigma2(cpu, mean)
            timecounter+=1
            debug_msg("avg process CPU usage: %d" % mean)
            debug_msg("variance is: %d" % sigma2)
    
            decider.update(mean, sigma2, timecounter)
        
            #if votes < 0:
            #    votes = 0
            if decider.isQuorumReached():
                debug_msg("Quorum reached, killing process")
                kill_proc_and_exit(p)
                if save_arg and decider.isSaveQuorumReached():
                    debug_msg("Interesting file found, saving testcase")
                    save_testcase(proc_arg)
        except psutil.NoSuchProcess:
            debug_msg("Checker lost the process")
            return
    debug_msg("timeout reached, killing the process and dying")
    if save_arg:
        debug_msg("Interesting file found, saving testcase")
        save_testcase(proc_arg)
    kill_proc_and_exit(p)

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
    
    debug_msg("starting search for process %s with args \"%s\"" % (exeFile, exeArgs))
       
    while True:
        pids = find_proc(exeFile, exeArgs)
        #actually better catch this, even if still early
        if pids != None:
            if len(pids) > 1:
                debug_msg("found %d process, will monitor %d" % (len(pids), pids[0] ))
            p=psutil.Process(pids[0])
            if not p.is_running():
                debug_msg('process dead before starting timer')
                return
            break
        if pids == None:
            debug_msg("process not found, keep searching")
        time.sleep(0.5)
     
    debug_msg("pid found: %d ; starting timer thread" % p.pid)
    timeout=threading.Event()
    threading.Thread(target=timer_thread, args=[timeout]).start()
    wait_for_proc(p.pid,timeout, proc_arg=exeArgs)

main()