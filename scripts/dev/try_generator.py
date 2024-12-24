from typing import Generator


class Foo:
    def __init__(self, total: int, mean: float):
        self.total = total
        self.mean = mean

    def __str__(self):
        return f"Foo(total={self.total}, mean={self.mean})"


def my_generator() -> Generator[int, str, Foo]:
    total = 0
    count = 0
    string = yield 0
    while string is not None:
        total += len(string)
        count += 1
        string = yield len(string)

    return Foo(total, total / count)


def main():
    gen = my_generator()
    try:
        print(next(gen))
        print(gen.send("hello"))
        print(gen.send("world"))
        print(gen.send(None))
    except StopIteration as e:
        print(e.value)


if __name__ == '__main__':
    main()
