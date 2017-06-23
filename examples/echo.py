#!/usr/bin/env python3
import sys
import logging

from jsbf import Bot


logging.basicConfig(level=logging.DEBUG)

signal_cli_binary = sys.argv[1]
signal_number = sys.argv[2]

bot = Bot(signal_cli_binary, signal_number)


@bot.handle('message')
def message_responder(message):
    logging.info("%s: %s", message['envelope']['source'], message['envelope']['dataMessage']['message'])
    return {
        "type": "send",
        "recipientNumber": message['envelope']['source'],
        "messageBody": message['envelope']['dataMessage']['message'],
        "id": "1"
    }


bot.run()
