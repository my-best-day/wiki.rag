"""
Iterator deque for lazy loading of elements and the ability to append to the left or right.
"""
from collections import deque
from typing import Iterable, Iterator, TypeVar

T = TypeVar("T")


class IteratorDeque(Iterator[T]):
    """
    A custom deque-like wrapper around an iterator to allow lazy loading of elements
    and the ability to append to the left or right.
    Supports traversing a collection while appending to the left or right during
    the traversal.

    deque = IteratorDeque(iterable)
    for item in deque:
        if condition:
            sub_items = get_sub_items(item)
            # in the next iteration, the sub_items will be traversed
            deque.extendleft(sub_items)
        else:
            process(item)
    """
    def __init__(self, iterable: Iterable[T]) -> None:
        """
        Initialize the IteratorDeque.
        Args:
            iterable (Iterable[T]): The iterable being wrapped.
        """
        self.left_queue = deque()
        self.right_queue = deque()
        self.iterator: Iterator = iter(iterable)

    def __iter__(self) -> Iterator[T]:
        """Return the iterator itself."""
        return self

    def __next__(self) -> T:
        """Return the next item from the iterator."""
        return self.popleft()

    def popleft(self) -> T:
        """
        Popleft from the left queue if it is not empty, otherwise return the
        next item from the iterator.
        """
        if self.left_queue:
            return self.left_queue.popleft()
        try:
            return next(self.iterator)
        except StopIteration:
            if self.right_queue:
                return self.right_queue.popleft()
            raise

    def extendleft(self, items: Iterator[T]) -> None:
        """
        Extend the left queue with the reversed items.
        """
        self.left_queue.extendleft(reversed(items))

    def appendleft(self, item: T) -> None:
        """
        Append an item to the left queue.
        """
        self.left_queue.appendleft(item)

    def appendright(self, item: T) -> None:
        """
        Append an item to the right queue.
        """
        self.right_queue.append(item)

    def popright(self) -> T:
        """
        Pop from the right queue - not supported.
        """
        raise NotImplementedError("popright is not supported")
