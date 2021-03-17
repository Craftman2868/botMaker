from os.path import exists as exist, isdir, join
from os import mkdir, chdir as cd, remove
from json import load as _load, dump as _dump

def readJson(path):
    with open(path, "r") as f: return _load(f)

def writeJson(path, data={}):
    with open(path, "w") as f: _dump(data, f, indent=4)

def mkfile(path, value=""):
    with open(path, "w") as f: f.write(value)