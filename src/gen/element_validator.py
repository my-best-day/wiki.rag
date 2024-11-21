"""
The ElementValidator validates that the offset and the length of the element
matches the actual bytes in the file. It reads the bytes from the file and
compares them to the bytes in the element.

It was built for the development to identify issues with the element generation.
The current implementation which is byte-centric made things quite simple.
Earlier attempts were in character / clean-text space and fail miserably.
"""
import logging
import argparse
from plumbing.handler import Handler
from gen.element.element import Element
from plumbing.chainable import Chainable
from xutils.byte_reader import ByteReader


logger = logging.getLogger(__name__)


class ElementValidator(Handler, Chainable):
    """
    The ElementValidator validates that the offset and the length of the element
    matches the actual bytes in the file. It reads the bytes from the file and
    compares them to the bytes in the element.

    It was built for the development to identify issues with the element generation.
    The current implementation which is byte-centric made things quite simple.
    Earlier attempts were in character / clean-text space and fail miserably.
    """
    def __init__(self, args: argparse.Namespace):
        Handler.__init__(self)
        Chainable.__init__(self)
        self.args: argparse.Namespace = args
        self._byte_reader = None

    @property
    def byte_reader(self) -> ByteReader:
        if self._byte_reader is None:
            self._byte_reader = ByteReader(self.args.text)
        return self._byte_reader

    def start(self):
        raise NotImplementedError("start method is not implemented")
        # super().start()

    def handle(self, element: Element):
        """
        Implements the Handler interface.
        Validates the element until a poison pill is received.
        """
        if element is not None:
            self.validate_element(element)
        else:
            logger.info("Received poison pill, forwarding None")
            self.cleanup()
            self.forward(None)

    def validate_element(self, element: Element):
        """
        validates the element by reading the bytes from the file and
        comparing them
        """
        snippet = self.byte_reader.read_bytes(element.offset, len(element.bytes))
        if snippet != element.bytes:
            caption = element.__class__.__name__

            raise ValueError(f"snippet does not match section at offset {element.offset}:\n"
                             f"{caption}: <<<{format_text(element.bytes)}>>>\n"
                             f"Snippet: <<<{format_text(snippet)}>>>")
        self.forward(element)

    def forward(self, element: Element):
        """
        Implements the Chainable interface. Forwards the element to the
        next handler.
        """
        super().forward(element)

    def cleanup(self):
        """not bullet proof, but something is better than nothing"""
        if self._byte_reader is not None:
            self._byte_reader.cleanup()
            self._byte_reader = None


def format_text(bytes: bytes) -> str:
    text = bytes.decode('utf-8')
    if len(text) > 200:
        m = 100
        return text[:m] + "...." + text[-m:]
    return text
