#
# borrowing some code from PEDA for GDB, by Long Le Dinh <longld at vnsecurity.net>
#

import time
import gdb
import re
from utils import *

REGISTERS = {
    8 : ["al", "ah", "bl", "bh", "cl", "ch", "dl", "dh"],
    16: ["ax", "bx", "cx", "dx"],
    32: ["eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp", "eip"],
    64: ["rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp", "rip",
         "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15"]
}

class GDBWrapper(object):

    ####################################
    #   GDB Interaction / Misc Utils   #
    ####################################
    def execute(self, gdb_command):
        """
        Wrapper for gdb.execute, catch the exception so it will not stop python script

        Args:
            - gdb_command (String)

        Returns:
            - True if execution succeed (Bool)
        """
        try:
            gdb.execute(gdb_command)
            return True
        except Exception as e:
            raise e
            #return False

    def execute_redirect(self, gdb_command, silent=False):
        """
        Execute a gdb command and capture its output

        Args:
            - gdb_command (String)
            - silent: discard command's output, redirect to /dev/null (Bool)

        Returns:
            - output of command (String)
        """
        result = None
        #init redirection
        if silent:
            logfd = open(os.path.devnull, "rw")
        else:
            logfd = tmpfile()
        logname = logfd.name
        gdb.execute('set logging off') # prevent nested call
        gdb.execute('set height 0') # disable paging
        gdb.execute('set logging file %s' % logname)
        gdb.execute('set logging overwrite on')
        gdb.execute('set logging redirect on')
        gdb.execute('set logging on')
        try:
            gdb.execute(gdb_command)
            gdb.flush()
            gdb.execute('set logging off')
            if not silent:
                logfd.flush()
                result = logfd.read()
            logfd.close()
        except Exception as e:
            gdb.execute('set logging off') #to be sure
            logfd.close()
            raise e
        return result.decode('ascii')
    
    #TODO
    def run(self):
        return
        
    
    def getarch(self):
        """
        Get architecture of debugged program

        Returns:
            - tuple of architecture info (arch (String), bits (Int))
        """
        arch = "unknown"
        bits = 32
        out = self.execute_redirect('maintenance info sections ?').splitlines()
        for line in out:
            if "file type" in line:
                arch = line.split()[-1][:-1]
                break
        if "64" in arch:
            bits = 64
        return (arch, bits)
        
    def get_status(self):
        """
        Get execution status of debugged program

        Returns:
            - current status of program (String)
                STOPPED - not being run
                BREAKPOINT - breakpoint hit
                SIGXXX - stopped by signal XXX
                UNKNOWN - unknown, not implemented
        """
        status = "UNKNOWN"
        out = self.execute_redirect("info program")
        for line in out.splitlines():
            #line=l.decode('ascii')
            if line.startswith("It stopped"):
                if "signal" in line: # stopped by signal
                    status = line.split("signal")[1].split(",")[0].strip()
                    break
                if "breakpoint" in line: # breakpoint hit
                    status = "BREAKPOINT"
                    break
            if "not being run" in line:
                status = "STOPPED"
                break
        return status
    
    def get_regs(self):
        return self.execute_redirect("i reg")
    
    def get_callstack(self):
        try:
            out = self.execute_redirect("i stack")
        except gdb.MemoryError:
            out = "can't access call stack context\n"
        return out
    
    def get_programcontext(self):
        return self.execute_redirect("i file")
        
    def get_codecontext(self):
        arch,bits = self.getarch()
        out=""
        try:
            if bits == 64:
                out += self.execute_redirect("x/i $rip")
            else: #32
                out += self.execute_redirect("x/i $eip")
        except gdb.MemoryError:
            out += "can't access pc\n"
        return out
        
    def get_stackcontext(self):
        arch,bits = self.getarch()
        out=""
        try:
            if bits == 64:
                out += self.execute_redirect("x/16xg $rsp-64")
            else: #32
                out += self.execute_redirect("x/16xw $esp-32")
        except gdb.MemoryError:
            out += "can't access stack context\n"
        return out

    def write_crashdump(self, prefix, path, echo=False):
        """
        write crashdump to /path/prefix-timestamp.txt,
        GDB.execute("x/16xg $rsp-64")
        """
        strtime=time.strftime('%d-%m-%y_%H%M%S')
        filename=prefix+"_"+strtime+'.txt'
        if os.path.exists(path+filename):
            i=1
            while True:    
                if not os.path.exists(path+filename + "-%d" % i):
                    filename += "-%d" % i
                    break
                i += 1
        try:
            crashfile=open(path+filename, 'w')
            out = self.get_programcontext()
            out+=self.get_regs()
            out+=self.get_callstack()
            out+=self.get_codecontext()
            out+=self.get_stackcontext()
            crashfile.write(out)
            if echo:
                self._print(out)
            crashfile.close()
        except:
            raise
        return True
    
    #if catch fork was set we can detect if we are about to follow fork, false if we are not following
    def detect_fork(self):
        out=self.execute_redirect("show follow-fork-mode")
        if "parent" in out:
            return False
        else:
            currPid=self.getpid()
            out=self.execute_redirect("i b")
            search = re.findall( "fork, process (\d+)", out )
            if len(search)>0 and currPid != int(search[0]):
                return int(search[0])
            else:
                return False
    
    def get_arguments(self):
        out = self.execute_redirect("show args")
        #Argument list to give program being debugged when it is started is "20".
        args = out.split("\"")[1:-1]
        if args == "":
            return None
        else:
            return args
        
    def _print(self, msg):
        gdb.write(msg+'\n')
        
    def debug_msg(self, msg):
        self._print('[GDB DEBUG] '+ msg)
        
    def getpid(self):
        out = self.execute_redirect('info proc')
        if out is None: # non-Linux or cannot access /proc, fallback
            out = self.execute_redirect('info program')
        out = out.splitlines()[0]
        if "process" in out or "Thread" in out:
            pid = out.split()[-1].strip(".)")
            return int(pid)
        else:
            return None