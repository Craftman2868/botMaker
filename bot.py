from files import exist, isdir, join, mkdir, mkfile, cd, remove
from config import Config
from error import ConfigError, FunctionError, CommandError
from importlib import import_module
from os.path import relpath, realpath
import sys
from discord import Client, Embed

def createEmbed(title, description,
            url=Embed.Empty, color=Embed.Empty,
            author=None, authorUrl=Embed.Empty, authorIcon=Embed.Empty,
            footer=Embed.Empty, footerIcon=Embed.Empty,
            image=Embed.Empty, thumbnail=Embed.Empty,
            fields={}
        ):
    e = Embed(title=title, description=description, url=url, color=color)
    if not author and authorIcon:
        author = title
        e.title = ""
    if author:
        e.set_author(name=author, url=authorUrl, icon_url=authorIcon)
    e.set_footer(text=footer, icon_url=footerIcon)
    if image:
        e.set_image(url=image)
    if thumbnail:
        e.set_thumbnail(url=thumbnail)
    for n, v in fields.items():
        e.add_field(name=n, value=v)
    return e

class Message:
    def __init__(self, bot, author, message):
        self.bot = bot
        self.author = author
        self.message = message
    def delete(self):
        self.bot.action("delete")
    def reply(self, *args):
        self.bot.action("reply", *args)
    def replyEmbed(self, *args, **kwargs):
        self.bot.action("embed", createEmbed(*args, **kwargs))
    def react(self, *reactions):
        self.bot.action("react", *reactions)

class Command(Message):
    def __init__(self, bot, cmd, author, message):
        super().__init__(bot, author, message)
        self.cmd = cmd
        self.args = message[len(self.bot.prefix)+len(self.cmd):].split(" ")

class Bot(Client):
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
            self.token = token
            mkfile(self.join("data", "token.txt"), self.token)
            mkdir(self.join("src"))
            mkfile(self.join("src", "main.py"))
        elif not isdir(self.path):
            raise NotADirectoryError(f"'{self.path}' isn't a directory")
        else:
            with open(self.join("data", "token.txt"), "r") as f: self.token = f.read()
        self.config = Config(self.join("data", "config.json"))
        self.manifest = Config(self.join("data", "manifest.json"), {"prefix": "<Your prefix>", "commands": {}, "events": {}})

        self.commands = self.manifest["commands"]
        self.events = self.manifest["events"]

        self.functionCache = {}

        self._actions = []

        super().__init__()
    @property
    def prefix(self):
        return self.manifest["prefix"]
    @prefix.setter
    def prefix(self, value):
        self.manifest["prefix"] = value
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
        return self.getFunction(name)(self, *args, **kwargs)
    def runCommand(self, name, *args):
        if name not in self.manifest["commands"]:
            raise CommandError(f"Command '{name}' not found")
        return self.runFunction(self.manifest["commands"][name], *args)
    def run(self):
        super().run(self.token)
    def action(self, name, *args):
        self._actions.append((name, args))
    __call__ = action
    def executeEvent(self, name, *args):
        if name in self.events:
           self.runFunction(self.events[name], *args)
    async def on_message(self, message):
        if message.author == self.user:
            return

        self.executeEvent("message", Message(self, message.author, message.content))
        for action in self._actions:
            name = action[0]
            args = action[1]
            if name == "reply":
                await message.channel.send(" ".join(args))
            elif name == "embed":
                await message.channel.send(embed=args[0])
            elif name == "delete":
                await message.delete()
            elif name == "react":
                for r in args:
                    await message.add_reaction(r)

        self._actions = []
        if message.content.startswith(self.prefix):
            msg = message.content[len(self.prefix):]
            for cmd in self.commands:
                if msg.startswith(cmd+" ") or msg == cmd:
                    self.runCommand(cmd, Command(self, cmd, message.author, message.content))
                    break
            else:
                self.executeEvent("commandNotFound", Message(self, message.author, message.content))
            
            for action in self._actions:
                name = action[0]
                args = action[1]
                if name == "reply":
                    await message.channel.send(" ".join(args))
                elif name == "embed":
                    await message.channel.send(embed=args[0])
                elif name == "delete":
                    await message.delete()
                elif name == "react":
                    for r in args:
                        await message.add_reaction(r)
            
            self._actions = []
    async def on_ready(self):
        print("Connected as "+str(self.user))
        self.executeEvent("ready")
