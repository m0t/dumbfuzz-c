#!/usr/bin/python3

import threading
import psutil
import time
import sys

debugFlag=True
processTimeout=20 #seconds

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
        sys.stdout.write('[MONITOR] ' + msg + '\n')
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

#wait until process is not busy ("define busy?")
#XXX blocking?
#things: set timeout, some files can really take time, save long running files in case, 
def wait_for_proc(pid, timeout):
    global debugFlag
    
    interval=1.0      #in second
    nslices=5
    
    votes=0
    quorum=1
    
    p = psutil.Process(pid)
    while not timeout.is_set():
        try:
            
            cpu=[]
            for i in range(0,nslices):
                cpu.append(p.get_cpu_percent())
                time.sleep(interval/nslices)
            mean=sum(cpu)/len(cpu)
            sigma2=getSigma2(cpu, mean)
            debug_msg("avg process CPU usage: %d" % mean)
            debug_msg("variance is: %d" % sigma2)
    
            #decision rules
            weight=0
            if mean == 0:
                weight += 0.3
            elif mean < 10:
                weight += 0.2
            elif mean > 50 and sigma2 > 100:
                weight -= 0.2
            if sigma2 == 0:
                weight += 0.2
            elif sigma2 <= 100:
                weight += 0.1
            elif sigma2 > 200:
                weight -= 0.2
            votes += weight
        
            if votes < 0:
                votes = 0
            if votes >= quorum:
                debug_msg("Quorum reached, killing process")
                p.kill()
                return
        except psutil.NoSuchProcess:
            debug_msg("Checker lost the process")
            return
    debug_msg("timeout reached, killing the process and dying")
    p.kill()

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
                debug_msg("found %d process, will use %d" % (len(pids), pids[0] ))
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
    wait_for_proc(p.pid,timeout)

main()