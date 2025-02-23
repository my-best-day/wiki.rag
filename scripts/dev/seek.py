import sys


def seek(path, offset, length):
    # seek stdin to position n
    with open(path, 'rb') as f:
        f.seek(0, 2)  # seek to end of file
        file_length = f.tell()  # get current position (file size)

        offset_before = max(0, offset - 100)
        end = offset + length
        end_after = min(file_length, end + 100)

        before_length = offset - offset_before
        after_length = end_after - end

        if before_length > 0:
            f.seek(offset_before)
            before = f.read(before_length)
        else:
            before = b'<EMPTY>'

        f.seek(offset)
        text = f.read(length)

        if after_length > 0:
            f.seek(end)
            after = f.read(after_length)
        else:
            after = b'<EMPTY>'

        before = strip_b_prefix(before)
        text = strip_b_prefix(text)
        after = strip_b_prefix(after)

        print(f"Before: {offset_before} {before_length} {'>' * 30}")
        print(before)
        print(f"Text: {offset} {length} {'-' * 30}")
        print(text)
        print(f"After: {end} {after_length} {'-' * 30}")
        print(after)
        print("<" * 50)


def strip_b_prefix(b: bytes) -> str:
    return str(b)[2:-1]


if __name__ == "__main__":
    path = sys.argv[1]
    offset = int(sys.argv[2])
    if len(sys.argv) > 3:
        length = int(sys.argv[3])
    else:
        length = 80
    seek(path, offset, length)
