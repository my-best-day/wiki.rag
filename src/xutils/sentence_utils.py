class SentenceUtils:

    @staticmethod
    def split_sentence(sentence, max_length):
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
