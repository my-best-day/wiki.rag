from gen.element.element import Element
from gen.element.section import Section


class Fragment(Section):
    """
    A Fragment is a fragment of a section. It adds a parent section attribute.
    """
    def __init__(self, parent: Section, offset: int, bytes: bytes):
        super().__init__(offset, bytes)
        self._parent_section = parent

    @property
    def parent_section(self) -> Section:
        return self._parent_section

    def to_data(self):
        data = super().to_data()
        data['parent'] = self.parent_section.to_data()
        return data

    def to_xdata(self):
        xdata = super().to_xdata()
        xdata['parent'] = self.parent_section.index
        return xdata

    @classmethod
    def from_data(cls, data):
        parent = Element.hierarchy_from_data(data['parent'])
        fragment = cls(parent, data['offset'], data['text'].encode('utf-8'))
        return fragment

    @classmethod
    def from_xdata(cls, xdata, byte_reader):
        parent_index = xdata['parent']
        parent = Element.instances[parent_index]
        offset = xdata['offset']
        start = offset - parent.offset
        end = start + xdata['length']
        _bytes = parent.bytes[start:end]
        fragment = cls(parent, offset, _bytes)
        return fragment
