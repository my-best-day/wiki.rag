"""
timer = Timer(caption='training')
sleep(2)
timer.step("step 1", restart=True)
# will return > training: step 1: 2.00s

sleep(3)

timer.step("step 2", restart=False)
# will return > training: step 2: 3.00s

sleep(5)

timer.step("step 3", restart=True)
# will return > training: step 3: 8.00s

timer.print('step 4', restart=True) # sugar for print(timer.step('step 4', restart=True))

timer.restart(title) # sugar for timer.step(title, restart=True)

def _time() is used internally to provide the time based on optional flag provided to
Timer constructor:
'performance' - time.perf_counter()
'process' - time.process_time()
'wall' - time.time()

which one should be the default?
"""
import os
import time
import logging
from typing import Optional, Union


class Timer:
    def __init__(self, caption: Optional[str] = None, time: str = 'performance') -> None:
        self._caption = caption
        self._time_type = time
        self._t0 = self._time()
        self._start_time = self._t0

    def elapsed(self, restart: bool = False) -> float:
        now = self._time()
        elapsed = now - self._start_time
        if restart:
            self._start_time = now
        return elapsed

    def total_time(self) -> float:
        now = self._time()
        elapsed = now - self._t0
        return elapsed

    def total(self, elapsed: Optional[float] = None) -> str:
        elapsed = elapsed if elapsed is not None else self.total_time()
        return self.format("total", elapsed)

    def step(self, title: Optional[str] = None, restart: bool = False) -> str:
        elapsed = self.elapsed(restart)
        return self.format(title, elapsed)

    def restart(self, title: Optional[str] = None) -> str:
        return self.step(title, restart=True)

    def print(self, title: Optional[str] = None, restart: bool = False) -> None:
        print(self.step(title, restart))

    def format(self, title: str, elapsed: float) -> str:
        if self._caption is None:
            caption = ""
        else:
            caption = f"{self._caption}: "
        if title is None:
            title = ""
        else:
            title = f"{title}: "
        return f"{caption}{title}{elapsed:.4f}s"

    def _time(self) -> Union[float, int]:
        if self._time_type == 'performance':
            return time.perf_counter()
        elif self._time_type == 'process':
            return time.process_time()
        elif self._time_type == 'wall':
            return time.time()
        else:
            raise ValueError(f"Unknown time type: '{self._time}'")

    def __enter__(self):
        self._start_time = self._time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        elapsed = self.elapsed()
        print(self.format("completed", elapsed))

    async def __aenter__(self):  # NOSONAR
        self._start_time = self._time()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):  # NOSONAR
        elapsed = self.elapsed()
        print(self.format("completed", elapsed))


class LoggingTimer(Timer):

    def __init__(self, caption: Optional[str] = None, time: str = 'performance',
                 logger=None, level="DEBUG"):
        super().__init__(caption, time)
        self.logger = logger if logger else logging.getLogger(__name__)
        self.level = self.get_logging_level(level)

    def get_logging_level(self, level: Union[str, int]) -> int:
        if isinstance(level, str):
            log_level_upper = level.upper()
            numeric_level = getattr(logging, log_level_upper)
        elif isinstance(level, int):
            numeric_level = level
        else:
            raise ValueError(f"Unknown logging level: '{level}'")

        return numeric_level

    def total_message(self, elapsed: Optional[float] = None) -> str:
        total_time = self.total_time() if elapsed is None else elapsed
        msg = super().total(total_time)
        return msg

    def total(
        self,
        elapsed: Optional[float] = None,
        level: Union[str, int, None] = None
    ) -> str:

        level = self.get_logging_level(level) if level is not None else self.level
        msg = self.total_message(elapsed)
        self.logger.log(level=level, msg=msg)
        return msg

    def step(self, title: Optional[str] = None, restart: bool = False) -> str:
        msg = super().step(title, restart)
        self.logger.log(level=self.level, msg=msg)
        return msg

    def log(self, title: Optional[str] = None, restart: bool = False) -> None:
        msg = self.step(title, restart)
        self.logger.log(level=self.level, msg=msg)

    def __exit__(self, exc_type, exc_value, traceback):
        elapsed = self.elapsed()
        self.logger.log(level=self.level, msg=self.format("completed", elapsed))

    async def __aexit__(self, exc_type, exc_value, traceback):  # NOSONAR
        elapsed = self.elapsed()
        self.logger.log(level=self.level, msg=self.format("completed", elapsed))


DEBUG_MODE = os.getenv("DEBUG", "0") == "1"  # Enable debugging based on an environment variable


def timeit(caption: Optional[str] = None):
    def decorator(func):
        if DEBUG_MODE:
            return func

        def wrapper(*args, **kwargs):
            nonlocal caption
            if caption is None:
                caption = func.__name__
            with Timer(caption):
                return func(*args, **kwargs)
        return wrapper

    return decorator


def log_timeit(caption: Optional[str] = None, logger=None, level="DEBUG"):
    def decorator(func):
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
