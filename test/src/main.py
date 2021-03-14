def test(bot, msg):
    msg.react("👍", "😎")
    msg.reply("J'ai réagi deux fois à ton message ! :sunglasses:")

def config(bot, message):
    if len(message.args) == 1:
        try:
            message.reply(bot.config[message.args[0]])
        except KeyError:
            message.reply(f"Configuration '{message.args[0]}' introuvable")
    elif len(message.args) == 2:
        bot.config[message.args[0]] = message.args[1]
        message.reply("La modification à bien été apportée !")

def clearConfig(bot, message):
    bot.config.clear()
    message.reply("La configuration à bien été effacée !")