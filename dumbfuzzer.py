import os


import logging as l
import configparser
from utils import *

class DumbFuzzer(object):
    logger = None
    settingsFile = "settings.ini"
    
    def __init__(self):
        self.debugFlag = False
        self.logFlag = True
        self.logFile = 'dumbfuzz.log'
        self.fuzzerPath = './radamsa.bin'
        self.fuzzIter = 200
        self.fuzzDst = './fuzzed'
        self.listfile = 'filelist.txt'
        self.loadSettings()
        
    def loadSettings(self):
        parser = configparser.SafeConfigParser()
        parser.read(self.settingsFile)
        
        try:
            if parser.has_option('dumbfuzz', 'debug'):
                self.debugFlag = parser.getboolean('dumbfuzz', 'debug')
            if parser.has_option('dumbfuzz', 'log_active'):
                self.logFlag = parser.getboolean('dumbfuzz', 'log_active')
            if parser.has_option('dumbfuzz', 'log_file'):
                self.logfile = parser.get('dumbfuzz', 'log_file')
            if parser.has_option('dumbfuzz', 'fuzzer_path'):
                self.fuzzerPath = parser.get('dumbfuzz', 'fuzzer_path')
            if parser.has_option('dumbfuzz', 'fuzz_iter'):
                self.fuzzIter = parser.getint('dumbfuzz', 'fuzz_iter')
            if parser.has_option('dumbfuzz', 'cases_list'):
                self.listfile = parser.get('dumbfuzz', 'cases_list')
        except configparser.NoSectionError as err:
            die("settings: " + err)
        #except ConfigParser.NoOptionError, err:
        #    self.debug_msg("settings: " + err)
            

    def debug_msg(self, msg):
        logger = self.logger
        #XXX this should be done better
        if self.logFlag:
            if self.logger == None:
                self.setup_logger()
            logger.warn(msg)
        if self.debugFlag:
            try:
                sys.stdout.write('[FUZZER] ' + msg + '\n')
            except BlockingIOError:
                logger.warn('detected IO error while writing to stdout')
        return

    def setup_logger(self):
        self.logger = l.getLogger("errorlog")
        if self.debugFlag:
            self.logger.setLevel(l.INFO)
        else:
            self.logger.setLevel(l.WARN)

        fh=l.FileHandler(self.logFile)
        if self.debugFlag:
            fh.setLevel(l.INFO)
        else:
            fh.setLevel(l.WARN)

        fmt=l.Formatter('%(asctime)s : %(levelname)s : %(message)s')
        fh.setFormatter(fmt)

        self.logger.addHandler(fh)
        return 

    #THIS RUN COMMANDS
    #testcase is the path to the testcase
    #write target files
    def fuzz_testcase(self,testcase):
        fuzzerPath = self.fuzzerPath
        fuzzDst=self.fuzzDst
        if not os.path.exists(fuzzDst):
            debug_msg("creating dir %s\n" % (fuzzDst))
            os.mkdir(fuzzDst)
        ext=get_ext(testcase)
        if debugFlag:
            fuzzCmd = "%s -v -n %d -o %s/fuzzed-%%n%s %s" % (fuzzerPath, fuzzIter, fuzzDst, ext, quotestring(testcase))
            debug_msg(fuzzCmd)
        else:
            fuzzCmd = "%s -n %d -o %s/fuzzed-%%n%s %s" % (fuzzerPath, fuzzIter, fuzzDst, ext, quotestring(testcase))
        ret = os.system(fuzzCmd)
        if (ret != 0):
            die("fuzzer failed to run")
        return

    def empty_fuzzdir(self):
        os.system("rm -rf %s/*" % self.fuzzDst)
    
    def getSettingsFile(self):
        return self.settingsFile
    
    def getFuzzDst(self):
        return self.fuzzDst
        
    def getCasesListFile():
        return self.listfile
        
class Target(object):
    settingsFile = 'settings.ini'
    debugProc = None
    monProc = None

    def __init__(self):
        self.loadSettings()

    def loadSettings(self):
        parser = configparser.SafeConfigParser()
        parser.read(self.settingsFile)
        try:
            self.exePath = parser.get('target', 'exePath')
            self.exeArgs = parser.get('target', 'exeArgs')
        except configparser.NoSectionError as err:
            die("settings: " + err)
        except configparser.NoOptionError as err:
            die("settings: " + err)

    def run(self, fuzzedcase):
        self.debugProc = subprocess.Popen("./launcher.py --batch --args %s %s %s" % (self.exePath, self.exeArgs, fuzzedcase), shell="/usr/bin/python")
        self.monProc = subprocess.Popen("./process_monitor.py %s %s" % (self.exePath, fuzzedcase), shell="/usr/bin/python")

    #blocker
    #will will monitor when target exits
    def wait(self):
        self.debugProc.wait()
        self.monProc.kill()

    def kill():
        self.debugProc.kill()
        self.monProc.kill()