# Janky Signal Bot Framework

A janky framework for building Signal bots. Requires [kbin76's fork of signal-cli](https://github.com/kbin76/signal-cli).


## Install
```
pip install git+https://github.com/JankySolutions/SignalBotFramework
```

Might put it in pypi eventually


## Usage

*See `examples/` folder for more complete examples, etc*

```python
from jsbf import Bot
bot = Bot('bin/signal-cli', '+12024561414')

@bot.handle('message')
def message_responder(message):
    logging.info("%s: %s", message['envelope'].get('source'), message['envelope']['dataMessage']['message'])
    return {
        "type": "send",
        "recipientNumber": message['envelope'].get('source'),
        "messageBody": message['envelope']['dataMessage']['message'],
        "id": "1"
    }


bot.run()
```

`Bot`'s constructor takes two arguments: the path to the signal-cli binary, and the number to use.

## Stability

none
