import logging
import argparse
from pathlib import Path
from gen.element.element import Element
from plumbing.handler import Handler
from plumbing.chainable import Chainable


logger = logging.getLogger(__name__)


class ByteReader:
    def __init__(self, path: Path):
        self.path = path
        self.file = open(path, "rb")

    def read(self, offset: int, size: int) -> bytes:
        self.file.seek(offset)
        return self.file.read(size)


def format_text(bytes: bytes) -> str:
    text = bytes.decode('utf-8')
    if len(text) > 200:
        m = 100
        return text[:m] + "...." + text[-m:]
    return text


class ElementValidator(Handler, Chainable):
    def __init__(self, args: argparse.Namespace):
        Handler.__init__(self)
        Chainable.__init__(self)
        self.args: argparse.Namespace = args
        self._reader = None

    @property
    def reader(self) -> ByteReader:
        if self._reader is None:
            self._reader = ByteReader(self.args.text)
        return self._reader

    def start(self):
        super().start()

    def handle(self, element: Element):
        logger.info("Handling element")
        if element is not None:
            self.validate_element(element)
        else:
            logger.info("Received poison pill, forwarding None")
            self.forward(None)

    def validate_element(self, element: Element):
        logger.info(f"Validating element {element}")
        snippet = self.reader.read(element.offset, len(element.bytes))
        if snippet != element.bytes:
            caption = element.__class__.__name__

            raise ValueError(f"snippet does not match section at offset {element.offset}:\n"
                             f"{caption}: <<<{format_text(element.bytes)}>>>\n"
                             f"Snippet: <<<{format_text(snippet)}>>>")
        self.forward(element)

    def forward(self, element: Element):
        logger.info(f"Forwarding {element} in {self.__class__.__name__}")
        super().forward(element)
