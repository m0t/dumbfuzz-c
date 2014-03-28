#!/usr/bin/python3

import threading
import psutil
import time
import sys

debugFlag=True
processTimeout=20 #seconds

def die(msg):
    sys.stderr.write( msg + "\n")
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
        sys.stdout.write('[MONITOR] ' + msg + '\n')
    return

#search the file in the name, then search other args in the cmdline
def find_proc(file, args):
    for proc in psutil.process_iter():
        if proc.name.find(file) >= 0:
            try:
                proc.cmdline.index(args)
                return proc.pid
            except ValueError:
                pass
    return None

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
        if not p.is_running():
            debug_msg("Checker lost the process")
            return
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

'''
def proc_checker(proc_dead):
    while not proc_dead.is_set():
        pid = find_proc()
        if pid != None:
            break
        #actually better catch this, even if still early
        if proc_dead.is_set():
            debug_msg('process dead before starting timer')
            return
    debug_msg("pid found: %d ; starting timer thread" % pid)
    timeout=threading.Event()
    threading.Thread(target=timer_thread, args=[timeout]).start()
    wait_for_proc(pid,timeout, proc_dead)
'''

def main():
    
    #checker_thread=threading.Thread(target=proc_checker, args=[proc_dead])
    #checker_thread.start()
    if len(sys.argv) != 3:
        die("%s <executable> <searchargs>" % sys.argv(0))
        
    exeFile=sys.argv(1)
    exeArgs=sys.argv(2)
       
    while True:
        pid = find_proc(exeFile, exeArgs)
        #actually better catch this, even if still early
        if not p.is_running():
            debug_msg('process dead before starting timer')
            return
        if pid != None:
            break
    debug_msg("pid found: %d ; starting timer thread" % pid)
    timeout=threading.Event()
    threading.Thread(target=timer_thread, args=[timeout]).start()
    wait_for_proc(pid,timeout)

main()