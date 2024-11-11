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

    def to_data(self):
        data = super(Section, self).to_data()
        data['text'] = self.text
        return data

    @classmethod
    def from_data(cls, data):
        section = cls(data['text'].encode('utf-8'))
        return section
