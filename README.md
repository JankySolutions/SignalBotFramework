# Janky Signal Bot Framework

A janky framework for building Signal bots. Requires [kbin76's fork of signal-cli](https://github.com/kbin76/signal-cli).


## Install
```
pip install git+https://github.com/JankySolutions/SignalBotFramework
```

Might put it in pypi eventually


## Usage

*See `examples/` folder for more complete examples, etc*


A simple example that responds to messages starting with "hi" with the text "Hello!"

```python
from jsbf import Bot

@bot.handle('^hi')
def message_responder(message):
    return {
        "type": "send",
        "recipientNumber": message['envelope']['source'],
        "messageBody": "Hello!",
        "id": "1"
    }


bot.run('+12024561414', 'bin/signal-cli')
```

`Bot`'s constructor takes two arguments: the path to the signal-cli binary, and the number to use.

## Stability

none
