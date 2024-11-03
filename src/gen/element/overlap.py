from gen.element.section import Section


class Overlap(Section):
    """
    An overlap is bytes without an offset.
    We derive from section, disabling offset.
    """

    def __init__(self, _bytes: bytes) -> None:
        super().__init__(offset=0, _bytes=_bytes)

    @property
    def offset(self) -> int:
        raise NotImplementedError
