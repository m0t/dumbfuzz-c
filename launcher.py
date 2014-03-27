#!/usr/bin/gdb -x 

import sys
import time
import threading
import psutil

try:
    sys.path.index('.')
except ValueError:
    sys.path.append(".")

import gdbwrapper

debugFlag = True
processTimeout=20 #seconds
#XXX, at some point, move everything in a launcher class
GDB=None

def timer_thread(event):
    global processTimeout
    time.sleep(processTimeout)
    event.set()

def getSigma2(l, mean):
    s2=[]
    for i in l:
        s2.append(i*i)
    return (sum(s2)/len(s2))-(mean*mean)

#wait until process is not busy ("define busy?")
#XXX blocking?
#things: set timeout, some files can really take time, save long running files in case, 
def wait_for_proc(pid, timeout, proc_dead):
    global debugFlag
    global GDB
    
    interval=1.0      #in second
    nslices=5
    threshold=20    #in percent
    p = psutil.Process(pid)
    while not timeout.is_set() and not proc_dead.is_set():
        if not p.is_running():
            GDB.debug_msg("Checker lost the process")
            return
        cpu=[]
        for i in range(0,nslices):
            cpu.append(p.get_cpu_percent())
            time.sleep(interval/nslices)
        mean=sum(cpu)/len(cpu)
        sigma2=getSigma2(cpu, mean)
        GDB.debug_msg("avg process CPU usage: %d" % mean)
        GDB.debug_msg("variance is: %d" % sigma2)
    
    if proc_dead.is_set():
        GDB.debug_msg('process dead')
        return
    GDB.debug_msg("timeout reached, killing the process and dying")
    p.kill()

#XXX one really bad thing: we never find a pid. process does not start. then what?
def proc_checker(proc_dead):
    global GDB
    while not proc_dead.is_set():
        try:
            pid = GDB.getpid()
        except gdb.error:
            pass
        if pid:
            GDB.debug_msg("pid found: %d ; starting timer thread" % pid)
            break
    #actually better catch this, even if still early
    if proc_dead.is_set():
        GDB.debug_msg('process dead')
        return
    timeout=threading.Event()
    threading.Thread(target=timer_thread, args=[timeout]).start()
    wait_for_proc(pid,timeout, proc_dead)

def main():
    global GDB
           
    #XXX: static args for testing
    gdbArgs='--impress --norestore'
    fpfile='fuzzed/fuzzed-100.ppt'

    GDB = gdbwrapper.GDBWrapper()

    GDB.execute("set disassembly-flavor intel")
    GDB.execute("handle SIGSEGV stop print nopass")

    GDB.debug_msg("starting checker thread")
    
    proc_dead = threading.Event()
    checker_thread=threading.Thread(target=proc_checker, args=[proc_dead])
    checker_thread.start()

    #gdb.execute("file %s" % exePath)
    #gdb.execute("r %s %s" % (gdbArgs,fpfile))
    GDB.execute('r')
    proc_dead.set()
    state = GDB.get_status()
    if state != 'STOPPED':
        #XXX save testcase with timestamp if we are here
        GDB.debug_msg('Crash detected, saving crashdump and testcase')
        GDB.write_crashdump('test', 'logs/', echo=True)
        sys.exit(1)
    else:
        GDB.debug_msg("Process terminated normally")
        sys.exit(0)

main()