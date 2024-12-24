"""
Use with coverage to get the time taken by each test case.

Usage:
    coverage run --source=src -m scripts.run_tests_with_timing

    % UNIT_TESTING=1 coverage run --source=src  scripts/run_tests_with_timing.py discover \
        -s tests/unit   > /tmp/foo.csv
"""
import unittest
import time
import sys


class TimedTestResult(unittest.TextTestResult):
    def startTest(self, test):
        self._started_at = time.time()
        super().startTest(test)

    def addSuccess(self, test):
        elapsed = time.time() - self._started_at
        print(f"{elapsed:.4f}, {test.id()}")
        super().addSuccess(test)

    def addFailure(self, test, err):
        elapsed = time.time() - self._started_at
        print(f"{elapsed:.4f}, {test.id()}")
        super().addFailure(test, err)

    def addError(self, test, err):
        elapsed = time.time() - self._started_at
        print(f"{elapsed:.4f}, {test.id()}")
        super().addError(test, err)


class TimedTestRunner(unittest.TextTestRunner):
    def _makeResult(self):
        return TimedTestResult(self.stream, self.descriptions, self.verbosity)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.discover('tests/unit')
    runner = TimedTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())
