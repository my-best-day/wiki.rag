class Proxy:
    def __init__(self, parent):
        self.parent = parent

    def __getattr__(self, name):
        return getattr(self.parent, f"_lol_{name}")


class Mother:
    def __init__(self):
        self.secret = "mine"


class Bar:
    def __init__(self):
        self.mother = Mother()
        self.header = Proxy(self)

    def __getattr__(self, name):
        return getattr(self.mother, name)

    @property
    def _lol_bar(self):
        print("ha ha ha")
        self._lol_bla

    @property
    def _lol_bla(self):
        self.mother.secret.decode('utf-8')


bar = Bar()
print(bar.secret)
bar.header.bar
