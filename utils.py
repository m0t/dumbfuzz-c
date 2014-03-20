import tempfile

def tmpfile(pref="dumbfuzz-"):
    """Create and return a temporary file with custom prefix"""
    return tempfile.NamedTemporaryFile(prefix=pref)