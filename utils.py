import tempfile

def tmpfile(pref="dumbfuzz-"):
    """Create and return a temporary file with custom prefix"""
    return tempfile.NamedTemporaryFile(prefix=pref)
    
def quotestring(s):
    return "\\'".join("'" + p + "'" for p in s.split("'"))

def get_ext(filename):
    return os.path.splitext(filename)[1]
    
def die(msg):
    sys.stderr.write("[ERROR] " + msg + "\n")
    sys.exit(-1)