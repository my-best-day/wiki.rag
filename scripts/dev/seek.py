import sys


def seek(path, n, a):
    # seek stdin to position n
    with open(path, 'rb') as f:
        f.seek(n - 80)
        before = f.read(80)
        overlap = f.read(20)
        f.seek(n)
        after = f.read(a)
        print(before)
        print("-" * 80)
        print(overlap)
        print("-" * 80)
        print(after)


if __name__ == "__main__":
    path = sys.argv[1]
    n = int(sys.argv[2])
    if len(sys.argv) > 3:
        a = int(sys.argv[3])
    else:
        a = 80
    seek(path, n, a)
