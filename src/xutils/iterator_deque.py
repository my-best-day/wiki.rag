from collections import deque
from typing import Iterable, Iterator, TypeVar

T = TypeVar("T")


class IteratorDeque(Iterator[T]):
    """
    A custom deque-like wrapper around an iterator to allow lazy loading of elements
    and the ability to append to the left or right.
    """
    def __init__(self, iterable: Iterable[T]) -> None:
        self.left_queue = deque()
        self.right_queue = deque()
        self.iterator: Iterator = iter(iterable)

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

    def extendleft(self, items: Iterator[T]) -> None:
        self.left_queue.extendleft(reversed(items))

    def appendleft(self, item: T) -> None:
        self.left_queue.appendleft(item)

    def appendright(self, item: T) -> None:
        self.right_queue.append(item)

    def popright(self) -> T:
        raise NotImplementedError("popright is not supported")

    def __bool__(self) -> bool:
        # TODO: remove this method in a few days
        raise NotImplementedError("bool operator is not supported")
