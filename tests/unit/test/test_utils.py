import unittest
from unittest.mock import patch
from xutils.utils import Utils


class TestUtils(unittest.TestCase):
    def test_is_truthy(self):
        with self.assertRaises(ValueError):
            Utils.is_truthy("what is this?")

    def test_is_env_var_truthy(self):
        with patch.dict('os.environ', {'fake_env_var': 'what is that?'}):
            with self.assertRaises(ValueError):
                Utils.is_env_var_truthy("fake_env_var")


if __name__ == '__main__':
    unittest.main()
