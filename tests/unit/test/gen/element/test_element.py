import unittest
from gen.element.element import Element


class TestElement(unittest.TestCase):

    def test_normalize_text_empty_string(self):
        self.assertEqual(Element.normalize_text(""), "")

    def test_normalize_text_clean_text(self):
        self.assertEqual(Element.normalize_text("abcDEF123 ,.!?'\"-"), "abcdef123 ,.!?'\"-")

    def test_normalize_text_special_characters(self):
        self.assertEqual(Element.normalize_text("ab@#$%^&*()cd"), "ab cd")

    def test_normalize_text_multiple_spaces(self):
        self.assertEqual(Element.normalize_text("  Multiple   Spaces  "), "multiple spaces")

    def test_normalize_text_mixed_case(self):
        self.assertEqual(Element.normalize_text("Mixed CASE text"), "mixed case text")

    def test_normalize_text_whitespace_characters(self):
        self.assertEqual(Element.normalize_text("Special\nCharacters\tAnd\rWhitespace"),
                         "special characters and whitespace")

    def test_normalize_text_non_ascii(self):
        self.assertEqual(Element.normalize_text("Café & Co."), "cafe co.")
        self.assertEqual(Element.normalize_text(
            # cspell:disable-next-line
            "Números en español: 1º 2º 3º"), "numeros en espanol 1 2 3")

    def test_normalize_text_long_input(self):
        n = 10
        m = 10
        long_input = "A" * n + "@#$%" * m + "Z" * n
        expected_output = "a" * n + " " + "z" * n
        self.assertEqual(Element.normalize_text(long_input), expected_output.strip())


if __name__ == '__main__':
    unittest.main()
