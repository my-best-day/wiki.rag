"""
Multi-purpose store for elements and segments.
"""
import json
from uuid import UUID
from pathlib import Path
from gen.element.element import Element
from xutils.byte_reader import ByteReader


class Store:
    _buffer_size = 100

    def store_elements(self, path: Path, elements: list[Element]) -> None:
        """
        Store elements in the store.
        """
        with open(path, 'w') as file:
            self.write_elements_to_handle(file, elements)

    def write_elements_to_handle(self, file, elements: list[Element]) -> None:
        buffer = []
        for element in elements:
            xdata = element.to_xdata()
            json_string = json.dumps(xdata)
            buffer.append(json_string)
            if len(buffer) >= Store._buffer_size:
                file.write('\n'.join(buffer) + '\n')
                buffer.clear()
        if buffer:
            file.write('\n'.join(buffer) + '\n')

    def load_elements(self, text_file_path: Path,
                      element_store_path: Path) -> None:
        byte_reader = ByteReader(text_file_path)
        with open(element_store_path, 'r') as file:
            self.load_elements_from_handle(byte_reader, file)

    def load_elements_from_handle(self, byte_reader, file) -> None:
        assert len(Element.instances) == 0, "Store already contains elements"
        xdata_list = []
        for line in file:
            json_strings = line.split('\n')
            for json_string in json_strings:
                if not json_string:
                    continue
                xdata = json.loads(json_string)
                Element.hierarchy_from_xdata(xdata, byte_reader)
                xdata_list.append(xdata)
        for xdata in xdata_list:
            uid = UUID(xdata['uid'])
            Element.instances[uid].resolve_dependencies(xdata)
