# botMaker

BotMaker est un programme permettant de créer un bot discord ultra simplement.

> Exemple:

test/data/manifest.json

```json
{
    "prefix": "!",
    "commands": {
        "test": "commands.test : test",
        "test2": "main: commande_test_2",
        "test3": "main:test3Command"
    },
    "events": {}
}
```

test/src/commands/test.py

```python
def test(bot, message):
    message.reply("Ceci est un test")
```

test/src/main.py

```python
def commande_test_2(bot, msg):
    msg.react("😃")

def test3Command(bot, m):
    msg.delete()
    msg.reply("j'ai supprimé ton message !")
```

terminal

```batch
python main.py test/
```

> Utilisation en ligne de commande

```bash
python main.py <path> [token]
```

- path: chemin du dossier où se trouve le bot (sera créer automatiquement s'il n'existe pas)

- token: token du bot discord (obligatoire pour créer le bot)

> Référence du manifest.json

|Nom|Type|Description|
|---|----|-----------|
|prefix|string|préfixe du bot|
|commands|dict|commandes du bot|
|event|dict|éventements du bot (pas encore fonctionnel)|
