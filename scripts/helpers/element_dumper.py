import logging
from gen.element.element import Element


logger = logging.getLogger(__name__)


def format_text(bytes: bytes) -> str:
    text = bytes.decode('utf-8')
    if len(text) > 200:
        m = 100
        return text[:m] + "...." + text[-m:]
    return text


class ElementDumper:
    def __init__(self, active: bool = True):
        super().__init__()
        self.active = active

    def handle(self, element: Element):
        if element is not None:
            if self.active:
                self.dump(element)
        else:
            logger.info("Received poison pill")

    def dump(self, element: Element):
        caption = element.__class__.__name__
        logger.info(f"{caption}: <<<{format_text(element.bytes)}>>>")
