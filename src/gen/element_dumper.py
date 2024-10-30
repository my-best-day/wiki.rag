import logging
from plumbing.handler import Handler
from gen.element.element import Element


logger = logging.getLogger(__name__)


def format_text(bytes: bytes) -> str:
    text = bytes.decode('utf-8')
    if len(text) > 200:
        m = 100
        return text[:m] + "...." + text[-m:]
    return text


class ElementDumper(Handler):
    def __init__(self):
        super().__init__()

    def handle(self, element: Element):
        self.dump(element)

    def dump(self, element: Element):
        caption = element.__class__.__name__
        logger.info(f"{caption}: <<<{format_text(element.bytes)}>>>")
