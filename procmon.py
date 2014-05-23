import threading
from decider import *

class Process(object):
    proc = None
    name = None
    args = None
    searchInterval = 0.5 
    
    def __init__(self, exename, args):
        self.name = exename
        self.args = args
 
    #search the file in the name, then search other args in the cmdline    
    def find_proc(self):
        pids=[]
        for proc in psutil.process_iter():
            if any(self.name in s for s in proc.cmdline()): #and not any(sys.argv[0] in s for s in proc.cmdline())
                if self.name.find(proc.name()) > 0:
                    if any(self.args in s for s in proc.cmdline()):
                        debug_msg("process pid is "+str(proc.pid))
                        pids.append(proc.pid)
        if len(pids) == 0:
            return None
        return pids
    
    #actually populate class finding the pid, will be blocked until is found
    def init(self):
        while True:
            pids = find_proc()
            #actually better catch this, even if still early
            if pids != None:
                if len(pids) > 1:
                    debug_msg("found %d process, will monitor %d" % (len(pids), pids[0] ))
                self.proc=psutil.Process(pids[0])
                if not self.proc.is_running():
                    debug_msg('process dead before starting timer')
                    return
                break
            if pids == None:
                debug_msg("process not found, keep searching")
            time.sleep(self.searchInterval)
    
    #a good example of proxy that is never used
    def get_pid(self):
        return self.proc.pid


class ProcMon(object):
    pipename="/tmp/monitor_pipe0"
    savedir="saved"
    debugFlag=True
    save_arg=True #will affect decision to save or not long running testcases
    processTimeout=20
    timeout=None
    pipe_event=None
    timer=None
    listener=None
    process=None
    
    def __init__(self, exeFile, exeArgs):
        timeout=threading.Event()
        pipe_event=threading.Event()
        self.exeFile = exeFile
        self.exeArgs = exeArgs
        self.process = Process(self.exeFile, self.exeArgs)
        
    def timer_thread(self):
        time.sleep(self.processTimeout)
        self.timeout.set()
    
    def getSigma2(l, mean):
        s2=[]
        for i in l:
            s2.append(i*i)
        return (sum(s2)/len(s2))-(mean*mean)
    
    #run in his own thread, occasionally read pipe, if anything was written verify with stored data
    def monitor_listener():
        global pipename
        return

    #immediately kill and exit
    def kill_proc_and_exit(p):
        p.kill()
        debug_msg("exiting")
        sys.exit(0)
        
    def start(self):
        debug_msg("starting search for process %s with args \"%s\"" % (exeFile, exeArgs))

        self.process.init()

        debug_msg("pid found: %d ; starting timer thread" % p.pid)

        self.timer = threading.Thread(target=self.timer_thread)

        self.timer.start()

        self.wait_for_proc()  

    def check_dir(self):
        if not os.path.exists(self.savedir):
            debug_msg("saved dir not found, creating")
            try:
                os.mkdir(self.savedir)
            except PermissionError:
                debug_msg("saved dir creation failed, dying")
                sys.exit(-1)

    def save_testcase(self, casefile):
        self.check_dir()
        strtime=time.strftime('%d-%m-%y_%H%M')
        if os.path.isdir(casefile):
            savefile="fuzzedcases-"+strtime
            debug_msg('passed whole testcases folder, copying everything ')
            shutil.copytree(casefile, self.savedir+savefile)
        else:
            savefile="fuzzedcase-"+strtime
            debug_msg('Saving testcase to ' + savefile)
            shutil.copy(casefile, self.savedir+savefile)

    #wait until process is not busy (for definition of busy, see decider.py)
    def wait_for_proc(self):
    
        interval=1.0      #in second
        nslices=5
    
        decider = Decider(self.save_arg)
    
        #XXX get the internal process obj or proxying calls? maybe better the latter
        p=self.process.proc
        
        timecounter = 0
        while not self.timeout.is_set():
            try:
            
                cpu=[]
                for i in range(0,nslices):
                    cpu.append(p.get_cpu_percent())
                    time.sleep(interval/nslices)
                mean=sum(cpu)/len(cpu)
                sigma2=self.getSigma2(cpu, mean)
                timecounter+=1
                debug_msg("avg process CPU usage: %d" % mean)
                debug_msg("variance is: %d" % sigma2)
    
                decider.update(mean, sigma2, timecounter)
        
                if decider.isQuorumReached():
                    debug_msg("Quorum reached, killing process")
                    self.kill_proc_and_exit(p)
                    if self.save_arg and decider.isSaveQuorumReached():
                        debug_msg("Interesting file found, saving testcase")
                        self.save_testcase()
            except psutil.NoSuchProcess:
                debug_msg("Checker lost the process")
                return
        debug_msg("timeout reached, killing the process and dying")
        if self.save_arg:
            debug_msg("Interesting file found, saving testcase")
            self.save_testcase(proc_arg)
        self.kill_proc_and_exit()
        
        