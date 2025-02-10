"""
Fragment is a fragment of a section. It adds a parent section attribute.
"""
from uuid import UUID
from xutils.byte_reader import ByteReader
from gen.element.element import Element
from gen.element.section import Section


class Fragment(Section):
    """
    Fragment is a fragment of a section. It adds a parent section attribute.
    """
    def __init__(self, parent: Element, offset: int, _bytes: bytes, uid: UUID = None):
        """
        Initialize the fragment.
        """
        super().__init__(offset, _bytes, uid=uid)
        self.parent = parent

    def to_xdata(self) -> dict:
        """Convert the fragment to xdata."""
        xdata = super().to_xdata()
        xdata['parent_uid'] = str(self.parent.uid)
        return xdata

    @classmethod
    def from_xdata(cls, xdata: dict, byte_reader: ByteReader):
        """Create a fragment from xdata."""
        uid = UUID(xdata['uid'])
        parent_uid = UUID(xdata['parent_uid'])
        parent = Element.instances[parent_uid]
        offset = xdata['offset']
        length = xdata['length']
        _bytes = byte_reader.read_bytes(offset, length)
        fragment = cls(parent, offset, _bytes, uid=uid)
        return fragment
