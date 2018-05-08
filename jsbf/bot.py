import json
import re
import logging
import socket

try:
    import raven
except ImportError:
    raven = None

logger = logging.getLogger(__name__)


class Bot(object):

    handlers = []
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    def __init__(self, dsn=None):
        self.sentry = None
        if dsn is not None:
            if raven is None:
                logger.error("DSN specified but raven could not be imported! Errors will not be sent to sentry")
            else:
                self.sentry = raven.Client(dsn)

    def register_handler(self, handler, regex, group):
        if not isinstance(regex, re._pattern_type):
            regex = re.compile(regex)
        self.handlers.append((handler, regex, group))

    def handle(self, regex=None, group=None):
        regex = '' if regex is None else regex

        def decorator(f):
            self.register_handler(f, regex=regex, group=group)
            return f
        return decorator

    def _handle_message(self, message):
        responses = []
        if message['data']['dataMessage'] is not None:
            datamessage = message['data']['dataMessage']
            text = datamessage.get('message')
            group = datamessage.get('groupInfo')
            for handler in self.handlers:
                if (handler[2] is None or (handler[2] is False and group is None) or handler[2] == group):
                    match = handler[1].match(text)
                    if match is not None:
                        logger.debug("Running handler %s", handler[0].__name__)
                        try:
                            handler_response = handler[0](message)
                            if type(handler_response) == list:
                                responses += handler_response
                            elif handler_response is not None:
                                responses.append(json.dumps(handler_response))
                        except:
                            logger.exception("An error occured while running handler %s", handler[0].__name__)
                            if self.sentry is not None:
                                self.sentry.captureException()
        return responses

    def run(self, socket='/var/run/signald/signald.sock'):
        self.sock.connect(socket)
        logger.info("Connected to signald control socket")
        hooks = {"message": self._handle_message}
        while True:
            rawmsg = b""
            while not rawmsg.endswith(b'\n'):
                rawmsg += self.sock.recv(1)
            try:
                logger.debug("Read from signald: %s", rawmsg.decode())
                msg = json.loads(rawmsg.decode())
                msg_type = msg.get('type')
                responses = []
                if msg_type in hooks:
                    responses = hooks[msg_type](msg)
                else:
                    logger.debug('Received message with unknown type %s', msg_type)
                for response in responses:
                    logger.debug("Writing to signald: %s", response)
                    self.sock.send(json.dumps(response).encode())
                    self.sock.send(b"\n")
                    logger.debug("Sent!")
            except json.JSONDecodeError:
                logger.debug("Not valid json:\n%s", msg)
