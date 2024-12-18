"""
Multi-purpose store for elements and segments.
"""
import json
import logging
from uuid import UUID
from pathlib import Path
from gen.element.element import Element
from xutils.byte_reader import ByteReader

__import__("gen.element.element")
__import__("gen.element.section")
__import__("gen.element.header")
__import__("gen.element.paragraph")
__import__("gen.element.fragment")
__import__("gen.element.container")
__import__("gen.element.article")
__import__("gen.element.extended_segment")
__import__("gen.element.list_container")
__import__("gen.element.segment")


logger = logging.getLogger(__name__)


class Store:
    _buffer_size = 100

    def __init__(self, single_store: bool = True) -> None:
        self.single_store = single_store

    def store_elements(self, path: Path, elements: list[Element]) -> None:
        """
        Store elements in the store.
        """
        with open(path, 'w') as file:
            self.write_elements_to_handle(file, elements)

    def write_elements_to_handle(self, file, elements: list[Element]) -> None:
        buffer = []
        for element in elements:
            element_data = element.to_xdata()
            json_string = json.dumps(element_data)
            buffer.append(json_string)

            if len(buffer) >= Store._buffer_size:
                buffer_str = '\n'.join(buffer) + '\n'
                file.write(buffer_str)
                buffer.clear()

        if buffer:
            final_str = '\n'.join(buffer) + '\n'
            file.write(final_str)

    def load_elements(
        self,
        text_file_path: Path,
        element_store_path: Path
    ) -> None:
        """Load elements from a file using a byte reader."""
        byte_reader = ByteReader(text_file_path)
        with open(element_store_path, 'r') as file:
            self.load_elements_from_handle(byte_reader, file)

    def load_elements_from_handle(self, byte_reader, file) -> None:
        """Load elements from a file handle and resolve their dependencies."""
        if self.single_store:
            assert len(Element.instances) == 0, "Store already contains elements"

        # First pass: Create elements
        element_data_list = []
        for line in file:
            element_data = json.loads(line)
            Element.hierarchy_from_xdata(element_data, byte_reader)
            element_data_list.append(element_data)

        # Second pass: Resolve dependencies
        for element_data in element_data_list:
            element_id = UUID(element_data['uid'])
            element = Element.instances[element_id]
            element.resolve_dependencies(element_data)
