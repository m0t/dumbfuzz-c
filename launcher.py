#!/usr/bin/gdb -x 

import os
import sys
import time
import shutil

try:
    sys.path.index('.')
except ValueError:
    sys.path.append(".")

#import additional settings
from gdbsettings import *

import gdbwrapper

class Launcher(object):
    logpath='logs/'
    pipename="/tmp/monitor_pipe0"
        
    def __init__(self):
        self.GDB = gdbwrapper.GDBWrapper()
        
    #XXX not a very good strategy
    def get_inputfile(self,args):
        inputfile = args[0].split(" ")[-1]
        self.GDB.debug_msg("input file should be %s" % inputfile)
        if os.path.isfile(inputfile) or os.path.isdir(inputfile):
            return inputfile
        return False

    def check_logdir(self):
        if not os.path.exists(self.logpath):
            self.GDB.debug_msg("logs dir not found, creating")
            try:
                os.mkdir(self.logpath)
            except PermissionError:
                self.GDB.debug_msg("log dir creation failed, dying")
                sys.exit(-1)

    #save testcase. if we passed the whole testcases folder, detect this and copy the whole bloody folder, 
    #
    def save_testcase(self,args):
    
        strtime=time.strftime('%d-%m-%y_%H%M')

        fuzzedcase = self.get_inputfile(args)
        if fuzzedcase:
            if os.path.isdir(fuzzedcase):
                savefile="fuzzedcases-"+strtime
                self.GDB.debug_msg('passed whole testcases folder, copying everything ')
                shutil.copytree(fuzzedcase, self.logpath+savefile)
            else:
                savefile="fuzzedcase-"+strtime
                self.GDB.debug_msg('Saving testcase to ' + savefile)
                shutil.copy(fuzzedcase, self.logpath+savefile)
        else:
            self.GDB.debug_msg("fuzzed case not found?")
    
    def pipe_send_message(self, msg):
        try:
            pipe=os.open(self.pipename, os.O_WRONLY|os.O_NONBLOCK)
        except:
            self.GDB.debug_msg("can't open pipe, probably not ready")
            return False
        try:
            #currently only one type of msg
            mesg=("PID:%s" % msg).encode('ascii')
            return os.write(pipe,mesg)
        except:
            self.GDB.debug_msg("pipe open, but couldn't write")
            #no point in doing anything
            return False
    
    def run(self):

        self.check_logdir()
        GDB=self.GDB
        GDB.execute("set disassembly-flavor intel")
        GDB.execute("handle SIGSEGV stop print nopass")
    
        for setting in gdbsettings:
            GDB.execute(setting)
    
        args = GDB.get_arguments()
        if args == None:
            GDB.debug_msg("No arguments to the executable")
        else: 
            GDB.debug_msg("Arguments for exe: %s" % " ".join(args)) #not really but fine 

        GDB.execute('r')
        while True:
            state = GDB.get_status()
            if state == 'BREAKPOINT':
                newPid = GDB.detect_fork()
                if newPid != False:
                    self.pipe_send_message(newPid)
                GDB.execute('c')
            else:
                break
        if state == 'STOPPED':
            GDB.debug_msg("Process terminated normally")
            sys.exit(0)
        else:
            #XXX more contextual naming for saved testcase
            GDB.debug_msg('Crash detected, saving crashdump and testcase')
            GDB.write_crashdump('fuzzlog', self.logpath, echo=True)
        
            #XXX extracting input file from args it's horrible
            self.save_testcase(args)
        
            #XXX second chance testing?
            GDB.execute('kill')
            sys.exit(1)

launcher=Launcher()
launcher.run()