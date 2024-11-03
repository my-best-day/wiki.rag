class EncodingUtils:
    """
    Utilities for encoding operations.
    """

    @staticmethod
    def adjust_split_point(_bytes: bytes, index: int, after_char: bool) -> int:
        """
        Adjust the split point to ensure it does not split a multi-byte character
        in the middle.

        args:
            _bytes (bytes): the bytes to split
            index (int): the index to split at
            after_char (bool): if True, the split point is after the character, otherwise
                it is before the character

        returns:
            int: the adjusted split point
        """
        if not EncodingUtils.index_in_bound(_bytes, index):
            raise ValueError(f"Index is out of bounds (ind: {index}, len: {len(_bytes)})")

        if index >= 0:
            adjusted_index = index
        else:
            adjusted_index = len(_bytes) + index

        try:
            _bytes[:adjusted_index].decode('utf-8')
        except UnicodeDecodeError as e:
            if after_char:
                adjusted_index = e.start + EncodingUtils.num_bytes_in_char(_bytes[e.start])
            else:
                adjusted_index = e.start

        if index < 0:
            adjusted_index = adjusted_index - len(_bytes)

        return adjusted_index

    @staticmethod
    def index_in_bound(array, index):
        return -len(array) <= index < len(array)

    @staticmethod
    def num_bytes_in_char(first_byte: int) -> int:
        """
        Return the number of bytes in the character at the given index.

        The number of bytes in a character is encoded in the first byte of the
        character.

        args:
            first_byte (int): the first byte of the character

        returns:
            int: the number of bytes in the character
        """
        if first_byte & 0x80 == 0x00:
            num_of_bytes_in_char = 1
        elif first_byte & 0xE0 == 0xC0:
            num_of_bytes_in_char = 2
        elif first_byte & 0xF0 == 0xE0:
            num_of_bytes_in_char = 3
        elif first_byte & 0xF8 == 0xF0:
            num_of_bytes_in_char = 4
        else:
            raise ValueError("Invalid UTF-8 character start byte")

        return num_of_bytes_in_char
