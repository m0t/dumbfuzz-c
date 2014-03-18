#!/usr/bin/gdb -x 
gdbArgs='--impress --norestore'
fpfile='fuzzed/fuzzed-100.ppt'
#gdb.execute("file %s" % exePath)
#gdb.execute("r %s %s" % (gdbArgs,fpfile))
gdb.execute("r")