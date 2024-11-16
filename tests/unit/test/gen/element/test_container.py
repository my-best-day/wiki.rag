import unittest
from gen.element.section import Section
from gen.element.container import Container


class TestContainer(unittest.TestCase):

    def setUp(self):
        self.section1 = Section(offset=42, _bytes=b'hello ')
        self.section2 = Section(offset=52, _bytes=b'world. ')

        # Create a concrete subclass of Container for testing
        class ConcreteContainer(Container):
            def __init__(self):
                super().__init__()
                self._elements = []
                self._offset = 0

            @property
            def elements(self):
                return iter(self._elements)

            def append_element(self, element):
                self._elements.append(element)

            @property
            def offset(self):
                return self._offset

        self.container_class = ConcreteContainer

    def test_append_element(self):
        container = self.container_class()
        element = Section(offset=10, _bytes=b'hello')
        container.append_element(element)
        self.assertEqual(list(container.elements), [element])

    def test_bytes_property(self):
        container = self.container_class()
        element1 = Section(offset=10, _bytes=b'hello')
        element2 = Section(offset=20, _bytes=b' world')
        container.append_element(element1)
        container.append_element(element2)
        self.assertEqual(container.bytes, b'hello world')

    def test_text_property(self):
        container = self.container_class()
        element1 = Section(10, b'hello')
        element2 = Section(20, b' world')
        container.append_element(element1)
        container.append_element(element2)
        self.assertEqual(container.text, 'hello world')

    def test_clean_text_property(self):
        container = self.container_class()
        element = Section(10, b'HELLO  WORLD')
        container.append_element(element)
        self.assertEqual(container.clean_text, 'hello world')

    def test_byte_length_property(self):
        container = self.container_class()
        element1 = Section(10, b'hello')
        element2 = Section(20, b' world')
        container.append_element(element1)
        container.append_element(element2)
        self.assertEqual(container.byte_length, 11)

    def test_char_length_property(self):
        container = self.container_class()
        element1 = Section(10, b'hello')
        element2 = Section(20, b' world')
        container.append_element(element1)
        container.append_element(element2)
        self.assertEqual(container.char_length, 11)

    def test_clean_length_property(self):
        container = self.container_class()
        element1 = Section(10, b'hello')
        element2 = Section(20, b' world')
        container.append_element(element1)
        container.append_element(element2)
        self.assertEqual(container.clean_length, 11)

    def test_abstract_methods(self):
        class BareContainer(Container):
            @property
            def elements(self):
                return super().elements

            @property
            def offset(self):
                return super().offset

            def append_element(self, element):
                super().append_element(element)

            def element_count(self):
                return super().element_count

        container = BareContainer()
        with self.assertRaises(NotImplementedError):
            container.elements
        with self.assertRaises(NotImplementedError):
            container.offset
        with self.assertRaises(NotImplementedError):
            container.append_element(None)
        with self.assertRaises(NotImplementedError):
            container.element_count()


if __name__ == '__main__':
    unittest.main()
