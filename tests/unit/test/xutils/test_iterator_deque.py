import unittest
from xutils.iterator_deque import IteratorDeque


class iter:
    def __init__(self, items):
        self.items = items

    def __next__(self):
        if not self.items:
            raise StopIteration
        return self.items.pop(0)

    def __iter__(self):
        return self

    def __bool__(self):
        return bool(self.items)


class TestIteratorDeque(unittest.TestCase):
    def test_basic_iteration(self):
        # Test basic iteration through the iterator
        numbers = iter([1, 2, 3])
        deque = IteratorDeque(numbers)
        self.assertEqual(list(deque), [1, 2, 3])

    def test_appendleft(self):
        numbers = iter([1, 2, 3])
        deque = IteratorDeque(numbers)
        deque.appendleft(0)
        self.assertEqual(list(deque), [0, 1, 2, 3])

    def test_appendleft_empty_iterator(self):
        deque = IteratorDeque(iter([]))
        deque.appendleft(0)
        self.assertEqual(list(deque), [0])

    def test_appendright(self):
        numbers = iter([1, 2, 3])
        deque = IteratorDeque(numbers)
        deque.appendright(4)
        self.assertEqual(list(deque), [1, 2, 3, 4])

    def test_appendright_empty_iterator(self):
        deque = IteratorDeque(iter([]))
        deque.appendright(4)
        self.assertEqual(list(deque), [4])

    def test_mixed_operations(self):
        numbers = iter([2, 3])
        deque = IteratorDeque(numbers)
        deque.appendleft(1)
        deque.appendright(4)
        deque.appendleft(0)
        self.assertEqual(list(deque), [0, 1, 2, 3, 4])

    def test_mixed_operation_empty_iterator(self):
        deque = IteratorDeque(iter([]))
        deque.appendright(1)
        deque.appendleft(0)
        self.assertEqual(list(deque), [0, 1])

    def test_empty_iterator(self):
        deque = IteratorDeque(iter([]))
        self.assertFalse(bool(deque))
        with self.assertRaises(StopIteration):
            next(deque)

    def test_none_iterator(self):
        with self.assertRaises(TypeError):
            IteratorDeque(None)

    def test_not_an_iterator(self):
        with self.assertRaises(TypeError):
            IteratorDeque("not an iterator")

    def test_bool_operator(self):
        # Test empty
        deque = IteratorDeque(iter([]))
        self.assertFalse(bool(deque))

        # Test with items in iterator
        deque = IteratorDeque(iter([1]))
        self.assertTrue(bool(deque))

        # Test with items in left queue
        deque = IteratorDeque(iter([]))
        deque.appendleft(1)
        self.assertTrue(bool(deque))

        # Test with items in right queue
        deque = IteratorDeque(iter([]))
        deque.appendright(1)
        self.assertTrue(bool(deque))

    def test_popleft_order(self):
        numbers = iter([2, 3])
        deque = IteratorDeque(numbers)
        deque.appendleft(1)
        deque.appendright(4)

        self.assertEqual(deque.popleft(), 1)
        self.assertEqual(deque.popleft(), 2)
        self.assertEqual(deque.popleft(), 3)
        self.assertEqual(deque.popleft(), 4)

        with self.assertRaises(StopIteration):
            deque.popleft()

    def test_popright_order(self):
        numbers = iter([2, 3])
        deque = IteratorDeque(numbers)
        self.assertRaises(NotImplementedError, deque.popright)

    def test_nested_iterators(self):
        numbers = iter([2, 3, 4])
        deque = IteratorDeque(numbers)
        nested = IteratorDeque(deque)
        deque.appendleft(1)
        nested.appendright(6)
        nested.appendleft(0)
        deque.appendright(5)
        self.assertEqual(list(nested), [0, 1, 2, 3, 4, 5, 6])


if __name__ == '__main__':
    unittest.main()
