import subprocess
import json
import logging
try:
    import raven
except ImportError:
    raven = None

logger = logging.getLogger(__name__)


class Bot(object):

    handlers = {}

    def __init__(self, binary, number, dsn=None):
        self.binary = binary
        self.number = number
        self.sentry = None
        if dsn is not None:
            if raven is None:
                logger.error("DSN specified but raven could not be imported! Errors will not be sent to sentry")
            else:
                self.sentry = raven.Client(dsn)

    def register_handler(self, msg_type, handler):
        if msg_type not in self.handlers:
            self.handlers[msg_type] = []
        self.handlers[msg_type].append(handler)

    def handle(self, msg_type):
        def decorator(f):
            self.register_handler(msg_type, f)
            return f
        return decorator

    def _handle_message(self, message):
        msg_type = message.get('type')
        logger.debug("Handling %s message", msg_type)
        responses = []
        if msg_type in self.handlers:
            for handler in self.handlers[msg_type]:
                logger.debug("Running %s handler %s", handler.__name__, msg_type)
                try:
                    handler_response = handler(message)
                    if handler_response is not None:
                        responses.append(json.dumps(handler_response))
                except:
                    logger.exception("An error occured while running %s handler %s", msg_type, handler.__name__)
                    if self.sentry is not None:
                        self.sentry.captureException()
        else:
            logger.debug("No handler for message type %s", msg_type)
        return responses

    def run(self):
        command = [self.binary, '-u', self.number, 'jsonevtloop']
        with subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE) as proc:
            logger.debug("Running %s...", command)
            while True:
                msg = proc.stdout.readline().decode()
                try:
                    responses = self._handle_message(json.loads(msg))
                    for response in responses:
                        logger.debug("Writing to signal-cli stdin: %s", response)
                        proc.stdin.write(response.encode('utf-8'))
                        proc.stdin.write(b"\r\n")
                        proc.stdin.flush()
                        logger.debug("Sent!")
                except json.JSONDecodeError:
                    logger.debug("Not valid json:\n%s", msg)
