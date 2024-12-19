import os
from distutils.util import strtobool


class Utils:
    @staticmethod
    def is_truthy(value):
        try:
            return bool(strtobool(str(value)))
        except ValueError:
            raise ValueError(f"Invalid strtobool value: {value}")

    @staticmethod
    def is_env_var_truthy(env_var):
        try:
            value = os.getenv(env_var, False)
            is_truthy = Utils.is_truthy(value)
            return is_truthy
        except ValueError as e:
            raise ValueError(f"Invalid strtobool value for {env_var}: {e}")
