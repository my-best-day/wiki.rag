import json
import random
import logging
import argparse
import pandas as pd
from typing import List
from pathlib import Path
from dataclasses import dataclass

from xutils.byte_reader import ByteReader
from xutils.iterator_deque import IteratorDeque
from xutils.overlap_setter import OverlapSetter

logger = logging.getLogger(__name__)


@dataclass
class DocumentData:
    uid: str
    title: str
    offset: int
    byte_length: int


class Document:
    def __init__(self, document_data: DocumentData, byte_reader: ByteReader):
        self.document_data = document_data
        self.byte_reader = byte_reader

    def __getattr__(self, name):
        return getattr(self.document_data, name)

    @property
    def bytes(self):
        return self.byte_reader.read_bytes(self.offset, self.byte_length)

    @property
    def text(self):
        return self.bytes.decode('utf-8')


class SegmentBuilder:
    def __init__(self, max_len: int) -> None:
        self.max_len = max_len
        self.base_length = int(0.8 * self.max_len)

    def segmentize_documents(self, doc_data_list: List[DocumentData]) -> List[List[bytes]]:
        doc_section_byte_list_list = []
        base_length = int(0.8 * self.max_len)
        for doc_data in doc_data_list:
            document_sections = self.segmentize_document(base_length, doc_data)
            doc_section_byte_list_list.append(document_sections)
            if len(doc_section_byte_list_list) % 5000 == 0:
                msg = f"processed {len(doc_section_byte_list_list)} / {len(doc_data_list)} docs"
                logger.info(msg)

        return doc_section_byte_list_list

    def segmentize_document(
        self,
        base_length: int,
        document_data: DocumentData
    ) -> List[bytes]:

        segment_count = (document_data.byte_length + base_length - 1) // base_length
        average_length = document_data.byte_length // segment_count if segment_count else 0
        document_bytes = document_data.bytes
        delimiter = b'\n'
        sentences = document_bytes.split(delimiter)
        sentences = [sentence + delimiter for sentence in sentences if sentence]
        sentence_iterator = IteratorDeque(iter(sentences))
        segment_byte_list = []
        segment_byte = b''
        rel_index = 0
        for sentence in sentence_iterator:
            if len(sentence) > base_length:
                # break into fragments and prepend to sentences
                try:
                    fragments = self.split_sentence(sentence, base_length)
                except ValueError:
                    logger.error(
                        "Could not split sentence of doc %s.%s: '%s'",
                        document_data.uid, rel_index, sentence
                    )
                    raise
                sentence_iterator.extendleft(fragments)
                logger.info(f"... sentence too long at document {document_data.uid}, fragments: "
                            f"{len(fragments)}")

            elif self.is_there_enough_room_in_mean_length(average_length, segment_byte, sentence):
                segment_byte += sentence
            elif self.is_there_enough_room_in_base_length_and_segment_is_short(
                    base_length, segment_byte, sentence):
                segment_byte += sentence
            else:
                segment_byte_list.append(segment_byte)
                segment_byte = sentence

        # add last segment
        if len(segment_byte) > 0:
            segment_byte_list.append(segment_byte)

        return segment_byte_list

    @staticmethod
    def is_sentence_too_long(base_length: int, sentence: str) -> bool:
        result = len(sentence) > base_length
        return result

    @staticmethod
    def is_there_enough_room_in_mean_length(
        avg_length: int,
        section: str,
        sentence: str
    ) -> bool:
        """is there a room for the next sentence within the average length?"""
        result = len(section) + len(sentence) <= avg_length
        return result

    @staticmethod
    def is_there_enough_room_in_base_length_and_segment_is_short(
        base_length: int,
        section: str,
        sentence: str
    ) -> bool:
        """if section is short, is there a room for the next sentence within the base length?"""
        is_short = len(section) <= 0.6 * base_length
        is_room_in_base_length = len(section) + len(sentence) <= base_length
        result = is_short and is_room_in_base_length
        return result

    @staticmethod
    def split_sentence(sentence, length):
        """
        split a sentence into fragments of a target length
        attempting to avoid splitted words between fragments.
        """
        logger.info("splitting sentence, length = %s", length)

        max_extend = 24
        frag_count = (len(sentence) + length - 1) // length
        target_length = (length // frag_count)
        safe_length = target_length - max_extend

        fragments = []
        if len(sentence) > length:
            for i in range(0, len(sentence), safe_length):
                fragments.append(sentence[i:i + safe_length])
        else:
            fragments.append(sentence)

        # find end of words at the end of a sentence and prepend to the next one
        for i in range(1, len(fragments)):
            j = 0
            fragment = fragments[i]
            length = len(fragment)
            max_steps = min(length, max_extend)
            while j < max_steps and not fragment[j:j + 1].isspace():
                j += 1
            if j < max_steps:
                j += 1
            fragments[i - 1] += fragment[:j]
            fragments[i] = fragment[j:]

            if j == max_steps:
                raise ValueError(
                    f"Could not find end of word for '{fragment}'"
                    f", length: {length}"
                    f", safe_length: {safe_length}"
                    f", target_length: {target_length}"
                    f", max_extend: {max_extend} "
                    f", max_steps: {max_steps} "
                    f", fragment index: {i} "
                )

        return fragments


def set_overlaps_for_document_list(max_len: int, doc_section_byte_list_list) -> List[List[bytes]]:
    section_with_overlap_list_list = []
    for doc_section_byte_list in doc_section_byte_list_list:
        section_with_overlap_list = set_overlaps_for_document(max_len, doc_section_byte_list)
        section_with_overlap_list_list.append(section_with_overlap_list)
    return section_with_overlap_list_list


def set_overlaps_for_document(max_len: int, doc_section_byte_list):
    section_with_overlaps_list = []

    section_count = len(doc_section_byte_list)
    prev_section_bytes = None
    for i in range(section_count):
        target_section_bytes = doc_section_byte_list[i]
        if i < section_count - 1:
            next_section_bytes = doc_section_byte_list[i + 1]
        else:
            next_section_bytes = None

        section_with_overlaps = OverlapSetter.add_overlaps(
            max_len,
            target_section_bytes,
            prev_section_bytes,
            next_section_bytes
        )

        section_with_overlaps_list.append(section_with_overlaps)

    return section_with_overlaps_list


# for debugging
def dump_document_section_list_list(plots_dir, max_len, document_byte_section_list_list):
    document_section_list_list = [
        [section.decode('utf-8') for section in doc_section_list]
        for doc_section_list in document_byte_section_list_list
    ]
    sections_json_path = plots_dir / f"sections_{max_len}.json"
    with open(sections_json_path, 'w') as json_file:
        json.dump(document_section_list_list, json_file)


def describe_document_sections(document_section_list_list, max_len):
    section_per_document = [len(section_list) for section_list in document_section_list_list]
    section_per_document_series = pd.Series(section_per_document)

    segment_lengths = [
        len(section)
        for doc_section_list in document_section_list_list
        for section in doc_section_list
    ]
    segment_lengths_series = pd.Series(segment_lengths)

    print("base length:", max_len)
    print("sections per document:\n", section_per_document_series.describe())
    print("segment lengths:\n", segment_lengths_series.describe())


def get_section_records(document_section_list_list):
    # create a dataframe with columns:
    # section index, document index, section offset, section length
    offset = 0
    section_records = []
    section_index = 0
    for doc_index, doc_section_list in enumerate(document_section_list_list):
        for rel_index, section_bytes in enumerate(doc_section_list):
            sec_length = len(section_bytes)
            section_data = (section_index, doc_index, rel_index, offset, sec_length)
            section_records.append(section_data)
            offset += sec_length
            section_index += 1
        offset += 6
    return section_records


def verify_sections(plots_dir, document_section_list_list, section_records):
    text_file_path = plots_dir / "plots"
    byte_reader = ByteReader(text_file_path)
    # keep: sample_records = section_records[:10]

    sample_records = []
    for record in section_records:
        # relative-index == 0 -> first section of document
        if record[2] == 0:
            sample_records.append(record)
            if len(sample_records) >= 20:
                break
    random_sample = random.sample(section_records, 20)
    sample_records.extend(random_sample)

    for (sec_ind, doc_ind, rel_ind, offset, length) in sample_records:
        reader_bytes = byte_reader.read_bytes(offset, length)
        doc_section_list = document_section_list_list[doc_ind]
        section_bytes = doc_section_list[rel_ind]

        is_match = section_bytes == reader_bytes
        if is_match:
            logger.debug("+ section %s of document %s rel index %s match",
                         sec_ind, doc_ind, rel_ind)
        else:
            logger.info("""
- section %s of document %s rel index %s does not match

expected: %s

actual  : %s
            """, sec_ind, doc_ind, rel_ind, section_bytes, reader_bytes)


def save_section_records(records, max_len):
    section_df = pd.DataFrame(
        records,
        columns=["section_index", "doc_index", "rel_index", "offset", "length"]
    )
    section_file_path = args.plots_dir / f"sections_{max_len}.csv"
    section_df.to_csv(section_file_path, index=False)
    logger.info("*** saved to %s", section_file_path)


def main(args):
    plots_file_path = args.plots_dir / "plots"
    plots_record_path = args.plots_dir / "plots_data.csv"

    byte_reader = ByteReader(plots_file_path)
    plots_df = pd.read_csv(plots_record_path, index_col=False)

    document_list = []
    for record in plots_df.values:
        document_data = DocumentData(*record)
        document = Document(document_data, byte_reader)
        document_list.append(document)

    max_len = args.max_len
    segment_builder = SegmentBuilder(max_len)
    document_section_list_list = segment_builder.segmentize_documents(document_list)
    # dump_document_section_list_list(args.plots_dir, max_len, document_section_list_list)

    describe_document_sections(document_section_list_list, max_len)

    document_section_list_list = set_overlaps_for_document_list(
        max_len,
        document_section_list_list
    )

    describe_document_sections(document_section_list_list, max_len)

    section_records = get_section_records(document_section_list_list)
    verify_sections(args.plots_dir, document_section_list_list, section_records)
    save_section_records(section_records, max_len)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-pd", "--plots-dir", type=str, required=True)
    parser.add_argument("-m", "--max-len", type=int, required=True)
    args = parser.parse_args()

    plots_dir = Path(args.plots_dir)
    if not plots_dir.exists():
        parser.error(f"Plots directory {plots_dir} does not exist")
    args.plots_dir = plots_dir

    main(args)
