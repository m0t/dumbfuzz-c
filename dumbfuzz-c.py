#!/usr/bin/python3

'''
fuzzer script, it will:
- fuzz the testcases and create some fuzzed files, and for each of these:
- launch the gdb script (in its own process) which runs the target process and checks for faults
- launch the process_monitor script (in its own process) which check when it's to time to weed the unfruitful processes
'''

import subprocess
import optparse
import shutil
import os
import sys

import configparser
from utils import *
from dumbfuzzer import DumbFuzzer

#################################################

def cleanupscript(script):
    debug_msg("running cleanup script %s" % script)
    try:
        cleanup_proc = subprocess.Popen("./%s" % script, shell="/usr/bin/bash")
        cleanup_proc.wait()
    except:
        debug_msg("error trying to run cleanup script")

def parse_args():
    parser = optparse.OptionParser("%prog [some opts] [-L filelist]|[-D fuzzdir]")
    #parser.add_option("-v", "--debug", help="get debug output", action="store_true", dest="debug", default=True)
    parser.add_option("-s", "--export", help="save filelist.txt ", action="store_true", dest="saveList", default=False)
    parser.add_option("-R", "--runonly", help="don't fuzz, run program on test files directly", action="store_true", dest="runonly", default=False)
    parser.add_option("-S", "--skipto", help="skip to #n iteration", dest="skipto", default=None)
    parser.add_option("-L", "--list", help="read filelist from file", dest="filelist", default=None)
    parser.add_option("-D", "--fuzzdir", help="create filelist from dir", dest="fuzzdir", default=None)
    parser.add_option("-N", "--noiterate", help="don't iterate generated fuzzed cases, pass whole folder", action="store_true", dest="noiterate", default=False)
    parser.add_option("-C", "--cleanup", help="run some script to cleanup after fuzz iteration", dest="cleanup", default=None)
    parser.add_option("-t", "--nofuzz", help="start fuzzer, dont generate testcases, for TESTING", action="store_true", dest="nofuzz", default=False)
    parser.add_option("-T", "--test", help="don't start fuzzer, for TESTING", action="store_true", dest="testrun", default=False)
    
    return parser.parse_args()

def loadTargetSettings(settingsFile):
    parser = configparser.SafeConfigParser()
    parser.read(settingsFile)
    try:
        exePath = parser.get('target', 'exePath')
        exeArgs = parser.get('target', 'exeArgs')
    except configparser.NoSectionError, err:
        die("settings: " + err)
    except configparser.NoOptionError, err:
        die("settings: " + err)
    
    return {'exePath': exePath, 'exeArgs': exeArgs}
        
def main():
    
    fuzzer=DumbFuzzer()
    settingsFile=fuzzer.getSettingsFile()
    targetOpts = loadTargetSettings(settingsFile)
    exePath = targetOpts['exePath']
    exeArgs = targetOpts['exeArgs']
    
    fuzzDst = fuzzer.getFuzzDst()
    
    opts, args = parse_args()
    
    if opts.filelist and opts.fuzzdir:
        die("options -L and -D are mutually exclusive")
    if not opts.filelist and not opts.fuzzdir:
        die("dickhead")
    if opts.fuzzdir:
        testcasesPath=opts.fuzzdir
        filelist=os.listdir(testcasesPath)
        filelist=[testcasesPath+'/'+ tc for tc in filelist]
    if opts.filelist:
        if opts.saveList:
            fuzzer.debug_msg("already loading from filelist, unsetting writing")
            opts.saveList = False
        try:
            lf=open(opts.filelist)
            filelist=lf.read().split('\n')
        except:
            die('Impossible to load file list, check file and syntax')
    
    if not filelist:
        die("no input files were specified")
    
    if opts.saveList:
        fuzzer.debug_msg("saving list of files to %s" % listfile)
        lf = open(listfile, 'w')
        lf.write("\n".join([str(i) for i in filelist]))
        lf.close()
    
    if opts.testrun:
        debug_msg("testrun only, exiting")
        sys.exit(0)
    
    if opts.cleanup:
        cscript=opts.cleanup
    
    try:
        start=0
        if opts.skipto:
            start=int(opts.skipto)
        for i in range(start,len(filelist)):
            f = filelist[i]
            if not opts.nofuzz and not opts.runonly:
                fuzzer.empty_fuzzdir(fuzzDst)
                debug_msg('fuzzing testcase #%d : %s' % (i,f))
                fuzzer.fuzz_testcase(f)
            if opts.noiterate:
                fuzzer.debug_msg("run target on fuzzed cases folder")
                gdb_proc = subprocess.Popen("./launcher.py --batch --args %s %s %s" % (exePath, exeArgs, fuzzDst), shell="/usr/bin/python")
                mon_proc = subprocess.Popen("./process_monitor.py %s %s" % (exePath, fuzzDst), shell="/usr/bin/python")

                gdb_proc.wait()
                mon_proc.kill()
            elif opts.runonly:
                fuzzer.debug_msg("run-only mode, will copy the file and run target directly on %s" % f)
                fuzzer.empty_fuzzdir(fuzzDst)
                fuzzedcase=fuzzDst + "/" + os.path.basename(f)
                shutil.copy(f, fuzzedcase)
                gdb_proc = subprocess.Popen("./launcher.py --batch --args %s %s %s" % (exePath, exeArgs, fuzzedcase), shell="/usr/bin/python")
                mon_proc = subprocess.Popen("./process_monitor.py %s %s" % (exePath, fuzzedcase), shell="/usr/bin/python")

                gdb_proc.wait()
                mon_proc.kill()
            else:
                for file in os.listdir(fuzzDst):            
                    fuzzedcase=fuzzDst + "/" + file
                    fuzzer.debug_msg("run target with file %s" % fuzzedcase)
                    gdb_proc = subprocess.Popen("./launcher.py --batch --args %s %s %s" % (exePath, exeArgs, fuzzedcase), shell="/usr/bin/python")
                    mon_proc = subprocess.Popen("./process_monitor.py %s %s" % (exePath, fuzzedcase), shell="/usr/bin/python")

                    gdb_proc.wait()
                    mon_proc.kill()
            fuzzer.debug_msg('Terminated fuzzing %s' % f)
            if  opts.nofuzz:
                fuzzer.debug_msg("nofuzz set, will not destroy testcases")
            else:
                fuzzer.empty_fuzzdir(fuzzDst)
            if opts.cleanup:
                cleanupscript(cscript)
            if opts.nofuzz:
                fuzzer.debug_msg("nofuzz set, will only do first iteration")
    except KeyboardInterrupt:
        fuzzer.debug_msg("Ctrl-c detected, exiting")
        try:
            gdb_proc.kill()
            mon_proc.kill()
        except:
            pass
        if cscript:
            cleanupscript(cscript)    
        sys.exit(0)


main()
