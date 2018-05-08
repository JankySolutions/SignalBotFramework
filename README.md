# Janky Signal Bot Framework

A janky framework for building Signal bots. Requires [signald](http://github.com/thefinn93/signald).


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
        "recipientNumber": message['data']['source'],
        "messageBody": "Hello!",
        "id": "1"
    }


bot.run()
```

`Bot`'s constructor takes one optional argument, a string to the path to the signald control socket.
It defaults to `/var/run/signald/signald.sock`, the signald default.

## Stability

Highly unstable, please get in touch or file an issue if you're planning on using this. Right now
I'm assuming no one uses it and may post breaking changes
