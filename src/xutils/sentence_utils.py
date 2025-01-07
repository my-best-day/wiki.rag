import re
from typing import List


class SentenceUtils:

    @staticmethod
    def split_sentence(sentence: bytes, max_length: int) -> List[bytes]:
        """
        split a sentence into fragments of a target length
        attempting to avoid splitted words between fragments.
        """
        if len(sentence) <= max_length:
            return [sentence]

        # up to max_extends bytes will be grabbed from the next fragment
        # to avoid splitting words
        max_extend = 24

        # split into balanced fragments
        fragment_count = (len(sentence) + max_length - 1) // max_length
        target_length = max_length // fragment_count
        safe_length = min(target_length, max_length - max_extend)

        # create the fragments
        fragments = []
        for i in range(0, len(sentence), safe_length):
            fragments.append(sentence[i:i + safe_length])

        # find end of words at the end of a sentence and prepend to the next one
        for i in range(1, len(fragments)):
            j = 0
            fragment = fragments[i]
            length = len(fragment)
            max_steps = min(length, max_extend)
            while j < max_steps and not fragment[j:j + 1].isspace():
                j += 1

            # if there is room, stick the space to the previous fragment
            if j < max_steps:
                j += 1

            fragments[i - 1] += fragment[:j]
            fragments[i] = fragment[j:]

        return fragments

    @staticmethod
    def split_bytes_into_sentences(text: bytes) -> list[bytes]:
        """
        Split the text into sentences (handles bytes instead of strings).

        If the text contains substrings "<prd>" or "<stop>", they would lead
        to incorrect splitting because they are used as markers for splitting.

        source: https://stackoverflow.com/questions/4576077/how-can-i-split-a-text-into-sentences

        Args:
            text (bytes): Text to be split into sentences.

        Returns:
            list[bytes]: List of sentences as bytes.
        """
        PRD = b'<prd>'

        def sub(pattern, repl, text):
            return re.sub(pattern, repl, text)

        # prefixes
        text = sub(br'(Mr|St|Mrs|Ms|Dr)\.(?=\b)', br'\1<prd>', text)

        # sub/domains (.com |google.com | io.google.com, etc.)
        text = sub(
            br'\b(?:[a-z0-9.-]+\.)+(com|net|org|io|gov|edu|me)\b',
            lambda m: m.group(0).replace('.', PRD),
            text
        )

        # decimal point
        text = sub(
            br'((?:[0-9])\.)+([0-9])',
            lambda m: m.group(0).replace('.', PRD),
            text
        )

        # Ph.D and Ph.D.
        text = sub(rb'\bPh\.D\.', b'Ph<prd>D<prd>', text)  # okay
        text = sub(rb'\bPh\.D\b', b'Ph<prd>D', text)  # okay

        # abbreviations and initials. e.g. John F. Kennedy, U.S. is best, the u.s.s.r. is lit
        text = sub(
            rb'(\b)((?:[A-Za-z]\.)+)(\s)',
            lambda m: m.group(1) + m.group(2).replace(b'.', PRD) + m.group(3),
            text
        )

        # suffixes
        text = sub(br'(\s)(Inc|Ltd|Jr|Sr|Co)\.', br'\1\2<prd>', text)

        # get .!? out of the quotes
        # \xe2\x80\x9d is the closing (windows) double quote
        text = sub(br'([.!?])(["\xe2\x80\x9d])', br'\2\1', text)

        # multiple dots
        text = sub(br'(\.+)\.', lambda match: PRD * len(match.group(1)) + b'.<stop>', text)

        # remaining dots are sentence terminators
        text = sub(br'([.?!])', br'\1<stop>', text)

        # bring back the dots
        text = sub(PRD, b'.', text)

        # split the text into sentences
        sentences = text.split(b'<stop>')

        return sentences
