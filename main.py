from sys import argv
from bot import Bot

try:
    path = argv[1]
except IndexError:
    print("Requied path")
    exit()

if len(argv) >= 3: token = argv[2]
else: token = None

try:
    bot = Bot(path, token)
except TypeError as e:
    if e.args[0] == "'token' argument is requied if bot don't exist":
        print("'token' argument is requied if bot don't exist")
        exit()
    else:
        raise

bot.run()