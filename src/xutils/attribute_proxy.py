class AttributeProxy:
    """A proxy class that facilitates attribute access on a parent object.

    If the parent object has an attribute `_parent_header`, it can be accessed
    as `article.parent.header` instead of `article._parent_header`. This is useful for
    maintaining a cleaner interface while encapsulating the underlying attribute naming
    conventions.
    """
    def __init__(self, parent, prefix):
        self.parent = parent
        self.prefix = prefix

    def __getattr__(self, name):
        return getattr(self.parent, f"{self.prefix}_{name}")
