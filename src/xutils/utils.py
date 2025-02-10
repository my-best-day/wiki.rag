"""
Utility functions.
"""
import os
import logging

logger = logging.getLogger(__name__)


class Utils:
    """
    Utility functions.
    """

    @staticmethod
    def is_truthy(value):
        """
        Check if a value is truthy.
        """
        try:
            return bool(Utils.strtobool(str(value)))
        except ValueError:
            logger.exception("Invalid strtobool value: %s", value)
            raise

    @staticmethod
    def is_env_var_truthy(env_var):
        """
        Check if an environment variable is truthy.
        """
        try:
            value = os.getenv(env_var, None)
            if value is None:
                return False
            is_truthy = Utils.is_truthy(value)
            return is_truthy
        except ValueError as e:
            logger.exception("Invalid strtobool value for %s: %s", env_var, e)
            raise

    @staticmethod
    def strtobool(val: str) -> int:
        """
        Convert a string to a boolean (int-based, matching `distutils.util.strtobool`).
        """
        val = val.lower()
        if val in ("y", "yes", "t", "true", "on", "1"):
            result = 1
        elif val in ("n", "no", "f", "false", "off", "0"):
            result = 0
        else:
            raise ValueError(f"Invalid truth value '{val}'")
        return result
