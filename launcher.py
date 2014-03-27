#!/usr/bin/gdb -x 

import sys
import time

try:
    sys.path.index('.')
except ValueError:
    sys.path.append(".")

import gdbwrapper

debugFlag = True

#XXX, at some point, move everything in a launcher class
GDB=None

def main():
    global GDB
           
    #XXX: static args for testing
    #gdbArgs='--impress --norestore'
    #fpfile='fuzzed/fuzzed-100.ppt'

    GDB = gdbwrapper.GDBWrapper()

    GDB.execute("set disassembly-flavor intel")
    GDB.execute("handle SIGSEGV stop print nopass")

    args = GDB.get_arguments()
    if args == None:
        GDB.debug_msg("No arguments to the executable")
    else: 
        GDB.debug_msg("Arguments for exe: %s" % " ".join(args)) #not really but fine 



    #gdb.execute("file %s" % exePath)
    #gdb.execute("r %s %s" % (gdbArgs,fpfile))
    GDB.execute('r')
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