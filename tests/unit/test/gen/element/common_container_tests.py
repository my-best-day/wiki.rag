from typing import Iterator
from gen.element.container import Container
from gen.element.element import Element


def common_container_tests(container: Container, elements: list[Element]):
    def test_elements_property_returns_iterator():
        assert isinstance(container.elements, Iterator)

    def test_bytes_property():
        assert container.bytes == b''.join(element.bytes for element in elements)

    def test_text_property():
        assert container.text == ''.join(element.text for element in elements)

    def test_clean_text_property():
        text = ''.join(element.text for element in elements)
        cleaned = Element.normalize_text(text)
        assert container.clean_text == cleaned

    def test_byte_length_property():
        assert container.byte_length == sum(element.byte_length for element in elements)

    def test_char_length_property():
        assert container.char_length == sum(element.char_length for element in elements)

    def test_clean_length_property():
        text = ''.join(element.text for element in elements)
        cleaned = Element.normalize_text(text)
        assert container.clean_length == len(cleaned)

    def test_reset_clears_cache():
        _ = container.bytes
        _ = container.text
        _ = container.clean_text
        elements[0]._bytes = b'modified'
        container.reset()
        expected_bytes = b''.join(element.bytes for element in elements)
        expected_text = ''.join(element.text for element in elements)
        expected_clean_text = Element.normalize_text(expected_text)
        assert container.bytes == expected_bytes
        assert container.text == expected_text
        assert container.clean_text == expected_clean_text

    return [
        test_elements_property_returns_iterator,
        test_bytes_property,
        test_text_property,
        test_clean_text_property,
        test_byte_length_property,
        test_char_length_property,
        test_clean_length_property,
        test_reset_clears_cache,
    ]
