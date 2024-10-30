from collections import deque
from typing import Iterator, TypeVar

T = TypeVar("T")


class IteratorDeque(Iterator[T]):
    """
    A custom deque-like wrapper around an iterator to allow lazy loading of elements
    and the ability to append to the left or right.
    """
    def __init__(self, iterator: Iterator[T]) -> None:
        if not isinstance(iterator, Iterator):
            raise TypeError("iterator must be an iterator")
        self.left_queue = deque()
        self.right_queue = deque()
        self.iterator = iterator

    def __iter__(self) -> Iterator[T]:
        return self

    def __next__(self) -> T:
        return self.popleft()

    def popleft(self) -> T:
        if self.left_queue:
            return self.left_queue.popleft()
        try:
            return next(self.iterator)
        except StopIteration:
            if self.right_queue:
                return self.right_queue.popleft()
            raise

    def appendleft(self, item: T) -> None:
        self.left_queue.appendleft(item)

    def appendright(self, item: T) -> None:
        self.right_queue.append(item)

    def popright(self) -> T:
        raise NotImplementedError("popright is not supported")

    def __bool__(self) -> bool:
        return bool(self.left_queue or self.right_queue or self.iterator)
