import threading
import psutil
import time
import os
import shutil
import sys

from decider import *
from libs_procmon import *
import configparser

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
            pids = self.find_proc()
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
            
    #TODO: pid has changed, class must be reinitialized with actual process data
    def update(self, newpid):
        try:
            self.proc=psutil.Process(newpid)
            #keep original name and args, we don't know what the target might execute, we just want to monitor the right pid
            #self.name=self.proc.cmdline()[0]
            #self.args=" ".join(self.proc.cmdline()[1:])
        except psutil.NoSuchProcess:
            debug_msg("trying to switch to a non existent pid")
            return False
        return True
    
    #we should use more this kind of stuff
    def get_pid(self):
        return self.proc.pid


class ProcMon(object):
    debugFlag=True
    save_arg=False #will affect decision to save or not long running testcases
    processTimeout=20
    readInterval=0.5    #seconds , inteval to check pipe
    timeout=None
    pipe_event=None
    listener=None
    process=None
    settingsFile = 'settings.ini'
    timer = None
    
    def __init__(self, exeFile, exeArgs):
        self.timeout=threading.Event()
        self.pipe_event=threading.Event()
        self.listener_death_signal=threading.Event()
        self.exeFile = exeFile
        self.exeArgs = exeArgs
        self.process = Process(self.exeFile, self.exeArgs)
        self.pipename="/tmp/monitor_pipe0"
        self.savedir="saved"
        self.loadSettings()
        
    def loadSettings(self):
        parser = configparser.SafeConfigParser()
        parser.read(self.settingsFile)

        try:
            if parser.has_option('procmon', 'debug'):
                self.debugFlag = parser.getboolean('procmon', 'debug')
            if parser.has_option('procmon', 'process_timeout'):
                self.processTimeout = parser.getint('procmon', 'process_timeout')
            if parser.has_option('procmon', 'pipename'):
                self.pipename = parser.get('procmon', 'pipename')
            if parser.has_option('procmon', 'savedir'):
                self.savedir = parser.get('procmon', 'savedir')
        except configparser.NoSectionError as err:
            die("settings: " + err)
     
    #XXX apparently timers are natively implemented in python, you should try that   
    def timer_thread(self):
        time.sleep(self.processTimeout)
        self.timeout.set()
        self.timer.join()
    
    def getSigma2(self, l, mean):
        s2=[]
        for i in l:
            s2.append(i*i)
        return (sum(s2)/len(s2))-(mean*mean)
    
    def check_pid(self, newPid):
        if self.process.get_pid() != newPid:
            debug_msg("target PID changed to %d, updating" % newPid)
            if self.process.update(newPid):
                self.pipe_event.set()        
    
    def parse_message(self, buf):
        lines=buf.splitlines()
        for line in lines:
            msg=line.split(":")
            if msg[0] == 'PID':
                self.check_pid(int(msg[1]))
    
    #run in his own thread, occasionally read pipe, if anything was written verify with stored data
    def monitor_listener(self):
        try:
            os.mkfifo(self.pipename)
        except:
            debug_msg("pipe was not created")
        try:
            pipe=os.open(self.pipename, os.O_RDONLY | os.O_NONBLOCK)
            debug_msg("Listener opened pipe")
        except:
            die("unable to open pipe")
        while not self.listener_death_signal.is_set():
            try:
                buf = os.read(pipe, 100)
            except:
                debug_msg("pipe read error")
                raise
            if len(buf) != 0:
                self.parse_message(buf.decode('ascii'))
            time.sleep(self.readInterval)
        try:
            os.close(pipe)
            os.unlink(self.pipename)
        except:
            pass

    def destroy_pipe(self):
        #try to close listener in the cool way
        self.listener_death_signal.set()
        self.listener.join()
        '''
        try:
            os.close(self.pipename)
            os.unlink(self.pipename) #XXX do we have to close the thread?
        except:
            pass
        '''
        
    def cleanup_and_exit(self, retvalue):
        self.destroy_pipe()
        debug_msg("exiting")
        self.timer.join()
        sys.exit(retvalue)

    #immediately kill and exit
    def kill_proc_and_exit(self):
        #XXX
        self.process.proc.kill()
        self.cleanup_and_exit(0)
        
    def start(self):
        debug_msg("starting search for process %s with args \"%s\"" % (self.exeFile, self.exeArgs))

        self.process.init()

        debug_msg("pid found: %d ; starting timer thread" % self.process.get_pid())

        self.timer = threading.Thread(target=self.timer_thread)
        self.listener = threading.Thread(target=self.monitor_listener)

        self.timer.start()
        self.listener.start()

        self.wait_for_proc()  

    def check_dir(self):
        if not os.path.exists(self.savedir):
            debug_msg("saved dir not found, creating")
            try:
                os.mkdir(self.savedir)
            except PermissionError:
                debug_msg("saved dir creation failed, dying")
                self.cleanup_and_exit(-1)

    def save_testcase(self):
        self.check_dir()
        casefile=self.exeArgs
        strtime=time.strftime('%d-%m-%y_%H%M')
        if os.path.isdir(casefile):
            savefile="fuzzedcases-"+strtime
            debug_msg('passed whole testcases folder, copying everything ')
            shutil.copytree(casefile, self.savedir+'/'+savefile)
        else:
            savefile="fuzzedcase-"+strtime
            debug_msg('Saving testcase to ' + savefile)
            shutil.copy(casefile, self.savedir+'/'+savefile)

    #wait until process is not busy (for definition of busy, see decider.py)
    def wait_for_proc(self):
    
        interval=1.0      #in second
        nslices=5
    
        decider = Decider(self.save_arg)
    
        #XXX get the internal process obj or proxying calls? maybe better the latter
        p=self.process.proc
        
        timecounter = 0
        while not self.timeout.is_set():
            if self.pipe_event.is_set():
                #XXX this shouldn't be needed
                p=self.process.proc
                debug_msg("watching now PID %d" % self.process.get_pid())
                self.pipe_event.clear()
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
                self.cleanup_and_exit(0)
        debug_msg("timeout reached, killing the process and dying")
        if self.save_arg:
            debug_msg("Interesting file found, saving testcase")
            self.save_testcase()
        self.kill_proc_and_exit()
        
        