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
