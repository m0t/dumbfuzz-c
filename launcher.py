#!/usr/bin/gdb -x 

import sys
import time
import threading

try:
    sys.path.index('.')
except ValueError:
    sys.path.append(".")

import gdbwrapper

#def proc_starter(GDB):

gdbArgs='--impress --norestore'
fpfile='fuzzed/fuzzed-100.ppt'

GDB = gdbwrapper.GDBWrapper()



#gdb.execute("file %s" % exePath)
#gdb.execute("r %s %s" % (gdbArgs,fpfile))
#starter_thread=threading.Thread(target=proc_starter, args=[GDB])
#starter_thread.start()
#pid = GDB.getpid()
GDB.execute("set disassembly-flavor intel")
GDB.execute("handle SIGSEGV stop print nopass")
GDB.execute('r')
state = GDB.get_status()
if state != 'STOPPED':
    #get context info, save to crashdump file, print some info, exit
    GDB.execute("i reg")
    GDB.execute("i stack")
    GDB.execute("x/16xg $rsp-64")
    sys.exit(1)
else:
    GDB.debug_msg("Process terminated normally")
    sys.exit(0)
