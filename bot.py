from files import exist, isdir, join, mkdir, mkfile, cd, remove
from config import Config
from error import ConfigError, FunctionError, CommandError
from importlib import import_module
from os.path import relpath, realpath
import sys
from discord import Client, Embed
from asyncio import run_coroutine_threadsafe


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
    def __init__(self, bot, message):
        self.bot = bot
        self._m = message
        self.author = self._m.author
        self.message = self._m.content
        self._r = None

    def __call__(self, coro, waitResult=False):
        if waitResult:
            while self._r:
                pass
            def cb(r):
                self._r = r
            self.bot(coro, cb)
            r = self._r
            self._r = None
            return r
        self.bot(coro, cb)

    def delete(self):
        self(self._m.delete())

    def reply(self, *args):
        return OwnMessage(self.bot, self(self._m.channel.send(content=" ".join(args)), True))

    def replyEmbed(self, *args, callback=None, **kwargs):
        return OwnMessage(self.bot, self(self._m.channel.send(embed=createEmbed(*args, **kwargs)), True))

    def react(self, *reactions):
        for r in reactions:
            self(self._m.add_reaction(r))

    def addReactListener(self, reaction, function):
        if self._m in self.bot._reactListeners:
            if reaction in self.bot._reactListeners[self._m]:
                if function not in self.bot._reactListeners[self._m][reaction]:
                    self.bot._reactListeners[self._m][reaction].append(
                        function)
            else:
                self.bot._reactListeners[self._m][reaction] = [function]
        else:
            self.bot._reactListeners[self._m] = {reaction: [function]}

    def addCommand(self, emoji, function):
        self.react(emoji)

        def f(bot, reaction):
            reaction.remove()
            function(bot, reaction)

        self.addReactListener(emoji, f)


class OwnMessage(Message):
    def edit(self, text):
        return OwnMessage(self.bot, self(self._m.edit(content=text)))


class Command(Message):
    def __init__(self, bot, cmd, message):
        super().__init__(bot, message)
        self.cmd = cmd
        self.args = self.message[len(
            self.bot.prefix)+len(self.cmd):].split(" ")


class Reaction:
    def __init__(self, bot, reaction, user):
        self.bot = bot
        self.emoji = reaction.emoji
        self.user = user
        if reaction.message.author == bot.user:
            self.message = OwnMessage(self.bot, reaction.message)
        else:
            self.message = Message(self.bot, reaction.message)

    def remove(self):
        self.bot.action(self.message, "removeReact")

    def react(self):
        self.message.react(self.emoji)


class Bot(Client):
    def __init__(self, path, token=None):
        self.path = realpath(path)
        sys.path.append(self.path)
        if not exist(self.path):
            if not token:
                raise TypeError(
                    "'token' argument is requied if bot don't exist")
            mkdir(self.path)
            mkdir(self.join("data"))
            self.token = token
            mkfile(self.join("data", "token.txt"), self.token)
            mkdir(self.join("src"))
            mkfile(self.join("src", "main.py"))
        elif not isdir(self.path):
            raise NotADirectoryError(f"'{self.path}' isn't a directory")
        else:
            with open(self.join("data", "token.txt"), "r") as f:
                self.token = f.read()
        self.config = Config(self.join("data", "config.json"))
        self.manifest = Config(self.join("data", "manifest.json"), {"prefix": "<Your prefix>", "commands": {}, "events": {}})

        self.commands = self.manifest["commands"]
        self.events = self.manifest["events"]

        self.functionCache = {}

        self._reactListeners = {}

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
            raise FunctionError(
                f"Function '{name}' not found in '{path}' module")
        except ModuleNotFoundError:
            raise FileNotFoundError(
                f"File '{self.join('src', path.replace('.', '/'))}.py' not found")

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

    def __call__(self, coro, callback=None):
        print("New task: "+coro.__name__)
        t = run_coroutine_threadsafe(coro, self.loop)

        def cb(t):
            print("End task: "+coro.__name__)
            if callback: callback(t.result())
        t.add_done_callback(cb)

    def executeEvent(self, name, *args):
        if name in self.events:
            self.runFunction(self.events[name], *args)

    async def on_message(self, message):
        if message.author == self.user:
            return

        self.executeEvent("message", Message(self, message))

        if message.content.startswith(self.prefix):
            msg = message.content[len(self.prefix):]
            for cmd in self.commands:
                if msg.startswith(cmd+" ") or msg == cmd:
                    self.runCommand(cmd, Command(self, cmd, message))
                    break
            else:
                self.executeEvent("commandNotFound", Message(self, message))

    async def on_reaction_add(self, reaction, user):
        if user == self.user:
            return
        for m in self._reactListeners:
            if m.id == reaction.message.id:
                message = m
                break
        else:
            return
        if reaction.emoji in self._reactListeners[message]:
            for f in self._reactListeners[message][reaction.emoji]:
                f(self, Reaction(self, reaction, user))

    async def on_ready(self):
        print("Connected as "+str(self.user))
        self.executeEvent("ready")
