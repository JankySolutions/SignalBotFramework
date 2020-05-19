import json
import re
import logging
import socket
import time

try:
    import raven
except ImportError:
    raven = None

logger = logging.getLogger(__name__)


class Bot(object):

    version = {}
    handlers = []

    def __init__(self, dsn=None):
        self.sentry = None
        if dsn is not None:
            if raven is None:
                logger.error("DSN specified but raven could not be imported! Errors will not be sent to sentry")
            else:
                self.sentry = raven.Client(dsn)

    def register_handler(self, handler, regex, group):
        try:
            pattern = re._pattern_type
        except AttributeError: # Python 3.7 on
            pattern = re.Pattern
        if not isinstance(regex, pattern):
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
        datamessage = message.get('data', {}).get('dataMessage')
        if datamessage is not None:
            text = datamessage.get('message')
            group = datamessage.get('groupInfo')
            if group:
                group = group.get('groupId')
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
                                responses.append(handler_response)
                        except:
                            logger.exception("An error occured while running handler %s", handler[0].__name__)
                            if self.sentry is not None:
                                self.sentry.captureException()
        return responses

    def _handle_accounts(self, data):
        logger.info(data)
        return [{"type": "subscribe", "username": a['username']} for a in data['data']['accounts']]

    def _handle_version(self, data):
        self.version = data['data']
        logger.info("Connected to {name} version {version} (branch {branch} commit {commit})".format(**self.version))
        return [{"type": "list_accounts"}]

    def run(self, s='/var/run/signald/signald.sock'):
        sleeptime = 1
        while True:
            try:
                self.connect(s)
                sleeptime = 1
            except Exception as e:
                logger.exception("aw shit it broke")
                logger.warn("Connection lost! Reconnecting in %s seconds...." % sleeptime)
                time.sleep(sleeptime)
                sleeptime = sleeptime*2 if sleeptime < 32 else sleeptime

    def connect(self, s):
        hooks = {
            "message": self._handle_message,
            "account_list": self._handle_accounts,
            "version": self._handle_version
        }
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(s)
        logger.info("Connected to signald control socket [%s]", s)
        while True:
            rawmsg = b""
            while not rawmsg.endswith(b'\n'):
                chunk = self.sock.recv(1)
                if len(chunk) == 0:
                    return None
                rawmsg += chunk
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
