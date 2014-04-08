#!/usr/bin/gdb -x 

import os
import sys
import time
import shutil

try:
    sys.path.index('.')
except ValueError:
    sys.path.append(".")

import gdbwrapper

debugFlag = True
logpath='logs/'
#XXX, at some point, move everything in a launcher class
GDB=None

#XXX not a very good strategy
def get_inputfile(args):
    inputfile = args[0].split(" ")[-1]
    GDB.debug_msg("input file should be %s" % inputfile)
    if os.path.isfile(inputfile):
        return inputfile
    return False

def check_logdir(logpath):
    if not os.path.exists(logpath)
        GDB.debug_msg("logs dir not found, creating")
    try:
        os.mkdir(logpath)
    except:
        GDB.debug_msg("log dir creation failed, dying")
        sys.exit(-1)

def main():
    global GDB
    global logpath

    GDB = gdbwrapper.GDBWrapper()

    check_logdir(logpath)

    GDB.execute("set disassembly-flavor intel")
    GDB.execute("handle SIGSEGV stop print nopass")

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
        GDB.write_crashdump('fuzzlog', logpath, echo=True)
        strtime=time.strftime('%d-%m-%y_%H%M')
        savefile="fuzzedcase-"+strtime
        GDB.debug_msg('Saving testcase to ' + savefile)
        fuzzedcase = get_inputfile(args)
        if fuzzedcase:
            shutil.copy(fuzzedcase, logpath+savefile)
        else:
            GDB.debug_msg("fuzzed case not found?")
        
        #XXX second chance testing?
        GDB.execute('kill')
        sys.exit(1)
    else:
        GDB.debug_msg("Process terminated normally")
        sys.exit(0)

main()