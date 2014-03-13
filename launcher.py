#!/usr/bin/gdb -x 
gdbArgs='--impress'
fpfile='/mnt/shared/ppt/2003gr9.ppt'
#gdb.execute("file %s" % exePath)
gdb.execute("r %s %s" % (gdbArgs,fpfile))