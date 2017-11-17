import subprocess
import json
import re
import logging

try:
    import raven
except ImportError:
    raven = None

logger = logging.getLogger(__name__)


class Bot(object):

    handlers = []

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
        if message.get('type') == "message" and not message.get('envelope', {}).get('isReceipt', True):
            logger.debug("Handling message")
            datamessage = message.get('envelope', {}).get('dataMessage', {})
            text = datamessage.get('message')
            group = datamessage.get('groupInfo')
            for handler in self.handlers:
                if (handler[2] is None or handler[2] == group is None):
                    match = handler[1].match(text)
                    if match is not None:
                        logger.debug("Running handler %s", handler[0].__name__)
                        try:
                            handler_response = handler[0](message)
                            if handler_response is not None:
                                responses.append(json.dumps(handler_response))
                        except:
                            logger.exception("An error occured while running handler %s", handler[0].__name__)
                            if self.sentry is not None:
                                self.sentry.captureException()
        return responses

    def run(self, number, binary='signal-cli'):
        command = [binary, '-u', number, 'jsonevtloop']
        with subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE) as proc:
            logger.debug("Running %s...", command)
            for msg in proc.stdout:
                msg = msg.decode().strip()
                try:
                    logger.debug("Read from signal-cli: %s", msg)
                    responses = self._handle_message(json.loads(msg))
                    for response in responses:
                        logger.debug("Writing to signal-cli stdin: %s", response)
                        proc.stdin.write(response.encode('utf-8'))
                        proc.stdin.write(b"\r\n")
                        proc.stdin.flush()
                        logger.debug("Sent!")
                except json.JSONDecodeError:
                    logger.debug("Not valid json:\n%s", msg)
