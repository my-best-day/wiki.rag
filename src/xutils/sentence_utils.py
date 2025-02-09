import re
import math
import logging
from typing import List, Tuple

from xutils.encoding_utils import EncodingUtils

logger = logging.getLogger(__name__)


class SentenceUtils:

    @staticmethod
    def split_sentence(sentence: bytes, max_length: int, max_extend: int = 24) -> List[bytes]:
        """
        Splits a sentence into fragments of approximately max_length,
        attempting to balance fragment sizes and avoid splitting words.

        Args:
            sentence (bytes): The input sentence to split.
            max_length (int): The maximum target byte length for fragments.
            max_extend (int): max bytes to grab from one fragment to the other

        Returns:
            List[bytes]: A list of sentence fragments.
        """
        if len(sentence) <= max_length:
            return [sentence]

        # split into balanced fragments
        sentence_length = len(sentence)
        fragment_count = (sentence_length + max_length - 1) // max_length
        target_length = math.ceil(sentence_length / fragment_count)

        # create the fragments
        fragments = []

        start = 0
        while start < len(sentence):
            end = min(len(sentence), start + target_length)
            end = EncodingUtils.adjust_split_point(sentence, end, after_char=True)
            fragment = sentence[start:end]
            fragments.append(fragment)
            start = end

        adjusted_fragments = SentenceUtils.adjust_fragments(fragments, max_extend)

        if b''.join(adjusted_fragments) != sentence:
            raise ValueError("adjusted_fragments do not reconstruct the original sentence")

        return adjusted_fragments

    @staticmethod
    def adjust_fragments(fragments: List[bytes], max_extend: int) -> List[bytes]:
        """
        Adjusts fragment boundaries to avoid splitting words by extending
        or shifting content between adjacent fragments.

        Args:
            fragments (List[bytes]): The initial list of fragments.
            max_extend (int): The maximum allowed extension to preserve words.

        Returns:
            List[bytes]: A list of adjusted fragments.
        """
        assert len(fragments) > 0
        adjusted_fragments = [fragments[0]]
        # find end of words at the end of a sentence and prepend to the next one
        for trailing_fragment in fragments[1:]:
            leading_fragment = adjusted_fragments.pop()
            adjusted_leading, adjusted_trailing = \
                SentenceUtils.adjust_fragment_pair(leading_fragment, trailing_fragment, max_extend)
            adjusted_fragments.append(adjusted_leading)
            adjusted_fragments.append(adjusted_trailing)
        return adjusted_fragments

    @staticmethod
    def adjust_fragment_pair(
        leading: bytes,
        trailing: bytes,
        max_extend: int
    ) -> Tuple[bytes, bytes]:
        """
        Adjusts a pair of fragments to avoid splitting words between them.

        Args:
            leading (bytes): The fragment preceding the split point.
            trailing (bytes): The fragment following the split point.
            max_extend (int): The maximum number of bytes allowed to shift.

        Returns:
            Tuple[bytes, bytes]: The adjusted fragments after boundary refinement.
        """
        if max_extend < 1:
            return leading, trailing

        # Goal is to stich together a word that was split between the two fragments.
        # We look for, in the trailing fragment, word bytes followed by non-word bytes followed
        # by at least one word byte. If we found that, subject to length limits, we move the
        # word bytes, and potentially the following non-word bytes, from the trailing to the
        # leading segment.

        adjusted_leading = None
        adjusted_trailing = None

        # (?:\w|(?:\xC0.)|(?:\xE0..)|(?:\xF0...) - \w capture ascii bytes while
        # the next three terms capture bytes of unicode characters with 2, 3, and 4 bytes
        # respectively
        # the \W makes sure we grab the entire word's end, the \w+ makes sure we
        # don't make trailing an empty fragment
        grab_leading_word_bytes_from_trailer = \
            rb'^((?:\w|(?:\xC0.)|(?:\xE0..)|(?:\xF0...)){1,%d})\W+' % max_extend + \
            rb'(?:\w|(?:\xC0.)|(?:\xE0..)|(?:\xF0...))+'

        # leading ends with a word byte
        if re.search(br'\w$', leading):
            # trailing starts with a word byte and matches \w+\W+\w+
            match = re.match(grab_leading_word_bytes_from_trailer, trailing)
            if match:
                remainder = match.group(1)
                adjusted_leading = leading + remainder
                adjusted_trailing = trailing[len(remainder):]

                room_left = max(0, max_extend - len(remainder))
                if room_left:
                    # grab non-word bytes trailing the word bytes found above
                    # and guaranteed to exist by the above regex
                    with_trailing_non_word_bytes = rb'(\W{1,%d})' % room_left
                    match = re.match(with_trailing_non_word_bytes, adjusted_trailing)
                    remainder = match.group(1)
                    adjusted_leading = adjusted_leading + remainder
                    adjusted_trailing = adjusted_trailing[len(remainder):]

        if adjusted_leading is None and adjusted_trailing is None:
            adjusted_leading = leading
            adjusted_trailing = trailing

        return adjusted_leading, adjusted_trailing

    @staticmethod
    def split_bytes_into_sentences(text: bytes) -> list[bytes]:
        """
        Split the text into sentences (handles bytes instead of strings).

        If the text contains substrings '<prd>' or '<stop>', they would lead
        to incorrect splitting because they are used as markers for splitting.

        source: https://stackoverflow.com/questions/4576077/how-can-i-split-a-text-into-sentences

        Args:
            text (bytes): Text to be split into sentences.

        Returns:
            list[bytes]: List of sentences as bytes.
        """
        PRD = b'<prd>'
        STOP = b'<stop>'

        def sub(pattern, repl, text):
            return re.sub(pattern, repl, text)

        # prefixes
        text = sub(br'(Mr|St|Mrs|Ms|Dr)\.(?=[\b\s])', br'\1<prd>', text)

        # sub/domains (.com |google.com | io.google.com, etc.)
        text = sub(
            br'\b(?:[a-z0-9.-]+\.)+(com|net|org|io|gov|edu|me)\b',
            lambda m: m.group(0).replace(b'.', PRD),
            text
        )

        # decimal point
        text = sub(
            br'((?:[0-9])\.)+([0-9])',
            lambda m: m.group(0).replace(b'.', PRD),
            text
        )

        # Ph.D and Ph.D.
        text = sub(rb'\bPh\.D\.', b'Ph<prd>D<prd>', text)  # okay
        text = sub(rb'\bPh\.D\b', b'Ph<prd>D', text)  # okay

        # abbreviations and initials. e.g. John F. Kennedy, U.S. is best, the u.s.s.r. is lit
        text = sub(
            rb'(\b)((?:[A-Za-z]\.)+)(?=\W)',
            lambda m: m.group(1) + m.group(2).replace(b'.', PRD),
            text
        )

        # suffixes
        text = sub(br'(\s)(Inc|Ltd|Jr|Sr|Co)\.', br'\1\2<prd>', text)

        # get .!? out of the quotes but mark it so we can reverse it
        # \xe2\x80\x9d is the closing (windows) double quote
        text = sub(br'([.!?]+)(["\xe2\x80\x9d])', br'<l-swap>\2<swap>\1<r-swap>', text)

        # multiple dots
        text = sub(br'(\.+)\.', lambda match: PRD * len(match.group(1)) + b'<prd><stop>', text)

        # remaining dots are sentence terminators
        text = sub(br'([.?!])', br'\1<stop>', text)

        # bring back the dots
        text = sub(PRD, b'.', text)
        text = sub(br'<l-swap>(["\xe2\x80\x9d])<swap>([.!?]+)(<stop>)?<r-swap>', br'\2\1\3', text)

        # spaces after stops trail the previous sentence
        text = sub(br'<stop>(\s+)', br'\1<stop>', text)

        # split the text into sentences
        sentences = text.split(STOP)

        return sentences
