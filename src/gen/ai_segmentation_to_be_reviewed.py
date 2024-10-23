from dataclasses import dataclass
from typing import Iterator, List, Optional
from math import ceil

@dataclass
class Element:
    bytes: bytes
    text: str
    clean_text: str
    offset: int
    bytes_length: int
    char_length: int
    clean_length: int

    def split(self, at_bytes: int) -> tuple['Element', 'Element']:
        # Mock implementation of split - you'll need to implement the actual logic
        first_bytes = self.bytes[:at_bytes]
        second_bytes = self.bytes[at_bytes:]
        # This is a simplification - you'll need to properly calculate all fields
        return (
            Element(first_bytes, "", "", self.offset, len(first_bytes), 0, 0),
            Element(second_bytes, "", "", self.offset + len(first_bytes), len(second_bytes), 0, 0)
        )

@dataclass
class Segment:
    pre_overlap: Optional[str]
    content: str
    post_overlap: Optional[str]
    clean_length: int


def segmentize(elements: Iterator[Element], max_clean_chars: int) -> Iterator[Segment]:
    """
    Split elements into segments with overlapping sections.

    Args:
        elements: Iterator of Element objects
        max_clean_chars: Maximum number of clean characters per segment

    Returns:
        Iterator of Segment objects with optional pre and post overlaps
    """
    min_overlap = ceil(0.1 * max_clean_chars)
    max_overlap = ceil(0.2 * max_clean_chars)

    current_text = ""
    current_clean_length = 0
    last_segment_overlap = None

    for element in elements:
        # If element is too long, split it
        if element.clean_length > max_clean_chars:
            # This is a simplification - you'll need to calculate the proper byte position
            estimated_bytes = int(max_clean_chars * (element.bytes_length / element.clean_length))
            first, second = element.split(estimated_bytes)
            # Put the first part in the current processing and the second back into processing
            element = first
            elements = iter([second] + list(elements))

        # If adding this element would exceed max length
        if current_clean_length + element.clean_length > max_clean_chars:
            # If we have accumulated text, create a segment
            if current_text:
                # Calculate post overlap if there's room
                post_overlap = None
                if current_clean_length < max_clean_chars:
                    overlap_size = min(
                        max_overlap,
                        max_clean_chars - current_clean_length,
                        element.clean_length
                    )
                    if overlap_size >= min_overlap:
                        post_overlap = element.clean_text[:overlap_size]

                yield Segment(
                    pre_overlap=last_segment_overlap,
                    content=current_text,
                    post_overlap=post_overlap,
                    clean_length=current_clean_length
                )

                # Start new segment with overlap if we had a post_overlap
                if post_overlap:
                    current_text = element.clean_text[len(post_overlap):]
                    current_clean_length = element.clean_length - len(post_overlap)
                    last_segment_overlap = post_overlap
                else:
                    current_text = element.clean_text
                    current_clean_length = element.clean_length
                    last_segment_overlap = None
            else:
                # If we have no accumulated text, start fresh with this element
                current_text = element.clean_text
                current_clean_length = element.clean_length
                last_segment_overlap = None
        else:
            # Add this element to current accumulation
            current_text += element.clean_text
            current_clean_length += element.clean_length

    # Don't forget remaining text
    if current_text:
        yield Segment(
            pre_overlap=last_segment_overlap,
            content=current_text,
            post_overlap=None,
            clean_length=current_clean_length
        )