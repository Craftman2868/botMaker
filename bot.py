from files import exist, isdir, join, mkdir, mkfile, cd, remove
from config import Config
from error import ConfigError, FunctionError, CommandError
from importlib import import_module
from os.path import relpath, realpath
import sys

class Bot:
    def __init__(self, path, token=None):
        self.path = realpath(path)
        sys.path.append(self.path)
        if not exist(self.path):
            if not token:
                raise TypeError("'token' argument is requied if bot don't exist")
            mkdir(self.path)
            mkdir(self.join("events"))
            mkdir(self.join("commands"))
            mkdir(self.join("data"))
            self.config = Config(self.join("data", "config.json"))
            self.manifest = Config(self.join("data", "manifest.json"), {"commands": [], "events": []})
            mkfile(self.join("data", "token.txt"), token)
            mkdir(self.join("src"))
        elif not isdir(self.path):
            raise NotADirectoryError(f"'{self.path}' isn't a directory")
        else:
            self.config = Config(self.join("data", "config.json"))
            self.manifest = Config(self.join("data", "manifest.json"), {"commands": [], "events": []})
        
        self.functionCache = {}
    def join(self, *paths):
        return join(self.path, *paths)
    def getFunction(self, name):
        if name in self.functionCache:
            return self.functionCache[name]
        data = name.split(":")
        if len(data) > 2:
            raise FunctionError(f"Invalid function '{name}'")
        if len(data) == 1:
            data.insert(0, "main")
        path = data[0].strip()
        name = data[1].strip()
        if not name.isidentifier():
            raise FunctionError(f"Invalid function name '{name}'")
        for f in path.split("."):
            if not f.isidentifier():
                raise FunctionError(f"Invalid function path '{path}'")
        try:
            f = getattr(import_module("src."+path), name)
        except AttributeError:
            raise FunctionError(f"Function '{name}' not found in '{path}' module")
        except ModuleNotFoundError:
            raise FileNotFoundError(f"File '{self.join('src', path.replace('.', '/'))}.py' not found")
        
        self.functionCache[path+":"+name] = f
        
        return f
    def runFunction(self, name, *args, **kwargs):
        self.getFunction(name)(self, *args, **kwargs)
    def runCommand(self, name, *args):
        if name not in self.manifest["commands"]:
            raise CommandError(f"Command '{name}' not found")
        return self.runFunction(self.manifest["commands"][name], *args)