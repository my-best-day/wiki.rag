"""
Utilities to measuring and logging elapsed times.
"""
import os
import time
import logging
from typing import Optional, Union


class Timer:
    """
    Timer for measuring and logging elapsed times.
    """
    def __init__(self, caption: Optional[str] = None, _time: str = 'performance') -> None:
        """
        Initialize the Timer.
        Args:
            caption (Optional[str]): The caption for the timer.
            _time (str): The type of time to use - see _time()
        """
        self._caption = caption
        self._time_type = _time
        self._t0 = self._time()
        self._start_time = self._t0

    def elapsed(self, restart: bool = False) -> float:
        """
        Get the elapsed time.
        Args:
            restart (bool): Whether to restart the timer.
        Returns:
            float: The elapsed time.
        """
        now = self._time()
        elapsed = now - self._start_time
        if restart:
            self._start_time = now
        return elapsed

    def total_time(self) -> float:
        """
        Get the total time.
        Returns:
            float: The total time.
        """
        now = self._time()
        elapsed = now - self._t0
        return elapsed

    def total(self, elapsed: Optional[float] = None) -> str:
        """
        Get the total time formatted as a string.
        Args:
            elapsed (Optional[float]): The elapsed time.
        Returns:
            str: The total time.
        """
        elapsed = elapsed if elapsed is not None else self.total_time()
        result = self.format("total", elapsed)
        return result

    def step(self, title: Optional[str] = None, restart: bool = False) -> str:
        """
        Get the elapsed time formatted as a string.
        Args:
            title (Optional[str]): The title for the elapsed time.
            restart (bool): Whether to restart the timer.
        Returns:
            str: The elapsed time.
        """
        elapsed = self.elapsed(restart)
        result = self.format(title, elapsed)
        return result

    def restart(self, title: Optional[str] = None) -> str:
        """
        Get the elapsed time formatted and restart the timer.
        Sugar for step(title, restart=True).
        Args:
            title (Optional[str]): The title for the elapsed time.
        Returns:
            str: The elapsed time.
        """
        return self.step(title, restart=True)

    def format(self, title: str, elapsed: float) -> str:
        """
        Format the elapsed time to a string with optional title.
        Args:
            title (str): The title for the elapsed time.
            elapsed (float): The elapsed time.
        Returns:
            str: The elapsed time.
        """
        if self._caption is not None:
            caption = f"{self._caption}: "
        else:
            caption = ""
        if title is None:
            title = ""
        else:
            title = f"{title}: "
        return f"{caption}{title}{elapsed:.4f}s"

    def _time(self) -> Union[float, int]:
        """
        Get the current time.
        Returns:
            Union[float, int]: The current time.
        """
        if self._time_type == 'performance':
            _time = time.perf_counter()
        elif self._time_type == 'process':
            _time = time.process_time()
        elif self._time_type == 'wall':
            _time = time.time()
        else:
            raise ValueError(f"Unknown time type: '{self._time}'")
        return _time


class LoggingTimer(Timer):
    """
    Timer that logs the elapsed time to a logger.
    """
    def __init__(self, caption: Optional[str] = None, _time: str = 'performance',
                 logger=None, level="DEBUG"):
        super().__init__(caption, _time)
        self.logger = logger if logger else logging.getLogger(__name__)
        self.level = self.get_logging_level(level)

    @staticmethod
    def get_logging_level(level: Union[str, int]) -> int:
        """
        Gets the logging level as an integer for the given level.
        Args:
            level (Union[str, int]): The logging level.
        Returns:
            int: The logging level.
        """
        if isinstance(level, str):
            log_level_upper = level.upper()
            numeric_level = getattr(logging, log_level_upper)
        elif isinstance(level, int):
            numeric_level = level
        else:
            raise ValueError(f"Unknown logging level: '{level}'")

        return numeric_level

    def total_message(self, elapsed: Optional[float] = None) -> str:
        """
        Get the total time formatted as a string.
        Args:
            elapsed (Optional[float]): The elapsed time.
        Returns:
            str: The total time.
        """
        total_time = self.total_time() if elapsed is None else elapsed
        msg = super().total(total_time)
        return msg

    def total(
        self,
        elapsed: Optional[float] = None,
        level: Union[str, int, None] = None
    ) -> str:
        """
        Log the total time.
        Args:
            elapsed (Optional[float]): The elapsed time.
            level (Union[str, int, None]): The logging level.
        Returns:
            str: The total time.
        """
        level = self.get_logging_level(level) if level is not None else self.level
        msg = self.total_message(elapsed)
        self.logger.log(level=level, msg=msg)
        return msg

    def step(self, title: Optional[str] = None, restart: bool = False) -> str:
        """
        Log the elapsed time.
        Args:
            title (Optional[str]): The title for the elapsed time.
            restart (bool): Whether to restart the timer.
        Returns:
            str: The elapsed time.
        """
        msg = super().step(title, restart)
        self.logger.log(level=self.level, msg=msg)
        return msg

    def log(self, title: Optional[str] = None, restart: bool = False) -> None:
        """
        Log the elapsed time.
        A synonym for step().
        Args:
            title (Optional[str]): The title for the elapsed time.
            restart (bool): Whether to restart the timer.
        """
        return self.step(title, restart)

    def __enter__(self):
        """
        Enter the context.
        """
        self._start_time = self._time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the context.
        """
        elapsed = self.elapsed()
        self.logger.log(level=self.level, msg=self.format("completed", elapsed))

    async def __aenter__(self):  # NOSONAR
        """
        Enter the context asynchronously.
        """
        self._start_time = self._time()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):  # NOSONAR
        """
        Exit the context asynchronously.
        """
        elapsed = self.elapsed()
        self.logger.log(level=self.level, msg=self.format("completed", elapsed))


DEBUG_MODE = os.getenv("DEBUG", "0") == "1"  # Enable debugging based on an environment variable


def log_timeit(caption: Optional[str] = None, logger=None, level="DEBUG"):
    """
    Decorator to log the time of a function.
    """
    def decorator(func):
        """
        Decorator to log the time of a function.
        """
        if DEBUG_MODE:
            return func

        def wrapper(*args, **kwargs):
            nonlocal caption
            if caption is None:
                caption = func.__name__
            with LoggingTimer(caption, logger=logger, level=level):
                return func(*args, **kwargs)
        return wrapper

    return decorator
