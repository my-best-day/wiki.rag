from typing import Tuple, Optional, Union

bytes_or_str = Union[bytes, str]


class EncodingUtils:
    """
    Utilities for encoding operations.
    """

    @staticmethod
    def split_at(
        text: bytes_or_str,
        index: int,
        after_char: bool = False,
        include_first: bool = True,
        include_remainder: bool = True
    ) -> Tuple[Optional[bytes_or_str], Optional[bytes_or_str]]:

        """
        Split the bytes/string into a first and remainder while adjusting the split point, if
        necessary, to avoid splitting in the middle of a multi-byte character.
        Args:
            byte_length: the length of the first fragment
            after_char: if True, the split point is after the character, otherwise it is before
            include_first: whether to include the first fragment
            include_remainder: whether to include the remainder fragment
        Returns:
            a tuple with the first and remainder fragment, or None if the caller does not
            want to generate one of the fragments
        """
        leading: bytes_or_str = None
        remainder: bytes_or_str = None

        # prevent splitting in the middle of a multi-byte character
        split_point = EncodingUtils.adjust_split_point(text, index, after_char)

        if include_first:
            leading = text[:split_point]

        if include_remainder:
            remainder = text[split_point:]

        return leading, remainder

    @staticmethod
    def adjust_split_point(
        text: bytes_or_str,
        index: int, after_char:
        bool,
        sign_mode: int = 1
    ) -> int:
        """
        Adjust the split point to ensure it does not split a multi-byte character
        in the middle.

        args:
            _bytes (bytes): the bytes to split
            index (int): the index to split at
            after_char (bool): if True, the split point is after the character, otherwise
                it is before the character
            sign_mode (int): If 1, always return a positive index (default).
              If 0, the returned index mimics the input index's sign.
              If -1, always return a negative index.


        returns:
            int: the adjusted split point
        """
        if not isinstance(index, int):
            raise TypeError(f"Index must be an int (got {type(index)} ({index}))")

        if not EncodingUtils.index_in_bound(text, index):
            raise ValueError(f"Index is out of bounds (ind: {index}, len: {len(text)})")

        adjusted_index = index if index >= 0 else len(text) + index

        if isinstance(text, bytes):
            try:
                text[:adjusted_index].decode('utf-8')
            except UnicodeDecodeError as e:
                if after_char:
                    adjusted_index = e.start + EncodingUtils.num_bytes_in_char(text[e.start])
                else:
                    adjusted_index = e.start

        # adjust the sign of the index
        if sign_mode == -1 or (sign_mode == 0 and index < 0):
            adjusted_index = adjusted_index - len(text)

        return adjusted_index

    @staticmethod
    def index_in_bound(array: list, index: int) -> bool:
        return -len(array) <= index <= len(array)

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
        if first_byte & 0xE0 == 0xC0:
            num_of_bytes_in_char = 2
        elif first_byte & 0xF0 == 0xE0:
            num_of_bytes_in_char = 3
        elif first_byte & 0xF8 == 0xF0:
            num_of_bytes_in_char = 4
        else:
            raise ValueError("Invalid UTF-8 character start byte")

        return num_of_bytes_in_char
