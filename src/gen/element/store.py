"""
Multi-purpose store for elements and segments.
"""
import json
from pathlib import Path
from gen.element.element import Element


class Store:
    def store_elements(self, path: Path, elements: list[Element]) -> None:
        """
        Store elements in the store.
        """
        buffer_size = 100
        buffer = []
        with open(path, 'w') as file:
            for element in elements:
                xdata = element.to_xdata()
                json_string = json.dumps(xdata)
                buffer.append(json_string)
                if len(buffer) >= buffer_size:
                    file.write('\n'.join(buffer) + '\n')
                    buffer.clear()
            if buffer:
                file.write('\n'.join(buffer) + '\n')

    def load_elements(self, path: Path) -> None:
        with open(path, 'r') as file:
            for line in file:
                json_strings = line.split('\n')
                for json_string in json_strings:
                    xdata = json.loads(json_string)
                    Element.hierarchy_from_xdata(xdata)
