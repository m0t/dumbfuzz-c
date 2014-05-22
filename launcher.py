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

debugFlag = True

#XXX, at some point, move everything in a launcher class
#GDB=None
class Launcher(object):
    def __init__(self):
        self.GDB = gdbwrapper.GDBWrapper()
        self.logpath='logs/'
        
    #XXX not a very good strategy
    def get_inputfile(self,args):
        inputfile = args[0].split(" ")[-1]
        self.GDB.debug_msg("input file should be %s" % inputfile)
        if os.path.isfile(inputfile):
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
    def save_testcase(self):
        #global GDB
        #global logpath
    
        strtime=time.strftime('%d-%m-%y_%H%M')
        savefile="fuzzedcase-"+strtime
        self.GDB.debug_msg('Saving testcase to ' + savefile)
        fuzzedcase = get_inputfile(args)
        if fuzzedcase:
            shutil.copy(fuzzedcase, self.logpath+savefile)
        else:
            self.GDB.debug_msg("fuzzed case not found?")
    
    def run(self):

        self.check_logdir(self.logpath)
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
        state = GDB.get_status()
        if state != 'STOPPED':
            #XXX more contextual naming for saved testcase
            GDB.debug_msg('Crash detected, saving crashdump and testcase')
            GDB.write_crashdump('fuzzlog', self.logpath, echo=True)
        
            strtime=time.strftime('%d-%m-%y_%H%M')
            savefile="fuzzedcase-"+strtime
            GDB.debug_msg('Saving testcase to ' + savefile)
            fuzzedcase = self.get_inputfile(args)
            if fuzzedcase:
                shutil.copy(fuzzedcase, self.logpath+savefile)
            else:
                GDB.debug_msg("fuzzed case not found?")
        
            #XXX second chance testing?
            GDB.execute('kill')
            sys.exit(1)
        else:
            GDB.debug_msg("Process terminated normally")
            sys.exit(0)

launcher=Launcher()
launcher.run()