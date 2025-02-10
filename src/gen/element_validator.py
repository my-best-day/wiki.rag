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
from typing import Union
from gen.element.element import Element
from xutils.byte_reader import ByteReader


logger = logging.getLogger(__name__)


class ElementValidator:
    """
    The ElementValidator validates that the offset and the length of the element
    matches the actual bytes in the file. It reads the bytes from the file and
    compares them to the bytes in the element.

    It was built for the development to identify issues with the element generation.
    The current implementation which is byte-centric made things quite simple.
    Earlier attempts were in character / clean-text space and fail miserably.
    """
    def __init__(self, args: argparse.Namespace):
        self.args: argparse.Namespace = args
        self._byte_reader = None

    @property
    def byte_reader(self) -> ByteReader:
        """Get and memoize the ByteReader."""
        if self._byte_reader is None:
            self._byte_reader = ByteReader(self.args.text)
        return self._byte_reader

    def validate_elements(self, elements: list):
        """
        Validates the elements until a poison pill is received.
        """
        for element in elements:
            self.handle(element)
        self.handle(None)

    def handle(self, element: Union[Element, None]):
        """
        Validates the element until a poison pill is received.
        """
        if element is not None:
            self.validate_element(element)
        else:
            self.cleanup()

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

    def cleanup(self):
        """not bullet proof, but something is better than nothing"""
        if self._byte_reader is not None:
            self._byte_reader.cleanup()
            self._byte_reader = None


def format_text(_bytes: bytes) -> str:
    """Format the text to a string of a max length of 200 characters."""
    text = _bytes.decode('utf-8')
    if len(text) > 200:
        m = 100
        return text[:m] + "...." + text[-m:]
    return text
