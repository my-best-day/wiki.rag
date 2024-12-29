#!/usr/bin/env python

import json
import random
import logging
import argparse
from pathlib import Path
from typing import List
import pandas as pd

from xutils.byte_reader import ByteReader

logger = logging.getLogger(__name__)


def verify_random_sections(plots_dir, n, document_section_list_list, section_records):
    text_file_path = plots_dir / "plots"
    byte_reader = ByteReader(text_file_path)

    # keep: sample_records = section_records[:10]
    sample_records = random.sample(section_records, n)
    verify_records(document_section_list_list, sample_records, byte_reader)


def verify_first_of_firsts(plots_dir, n, document_section_list_list, section_records):
    text_file_path = plots_dir / "plots"
    byte_reader = ByteReader(text_file_path)

    # keep: sample_records = section_records[:10]
    sample_records = []
    for record in section_records:
        # relative-index == 0 -> first section of document
        if record[2] == 0:
            sample_records.append(record)
            if len(sample_records) >= n:
                break

    verify_records(document_section_list_list, sample_records, byte_reader)


def verify_all_sections(plots_dir, document_section_list_list, section_records):
    text_file_path = plots_dir / "plots"
    byte_reader = ByteReader(text_file_path)

    verify_records(document_section_list_list, section_records, byte_reader)


def verify_records(document_section_list_list, sample_records, byte_reader):
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


# sec_index, doc_index, rel_index, offset, length
def read_section_records(plots_dir: str, max_len: int) -> List[List[int]]:
    """reads section records from a csv file"""
    section_file_path = plots_dir / f"sections_{max_len}.csv"
    section_df = pd.read_csv(section_file_path, index_col=False)
    section_records = section_df.values.tolist()
    return section_records


def read_section_dump(plots_dir: Path, max_len: int) -> List[List[bytes]]:
    """reads section strings from a json file, converts them to bytes"""
    section_file_path = plots_dir / f"sections_{max_len}.json"
    with open(section_file_path, 'r') as json_file:
        document_str_section_list_list = json.load(json_file)

    document_byte_section_list_list = convert_section_strings_to_bytes(
        document_str_section_list_list
    )
    return document_byte_section_list_list


def convert_section_strings_to_bytes(
    document_str_section_list_list: List[List[str]]
) -> List[List[bytes]]:

    document_byte_section_list_list = [
        [section.encode('utf-8') for section in doc_section_list]
        for doc_section_list in document_str_section_list_list
    ]
    return document_byte_section_list_list


def main(args):
    section_records = read_section_records(args.plots_dir, args.max_len)
    document_section_list_list = read_section_dump(args.plots_dir, args.max_len)
    if args.mode == "random":
        verify_random_sections(
            args.plots_dir,
            args.number,
            document_section_list_list,
            section_records
        )
    elif args.mode == "first":
        verify_first_of_firsts(
            args.plots_dir,
            args.number,
            document_section_list_list,
            section_records
        )
    elif args.mode == "all":
        verify_all_sections(
            args.plots_dir,
            document_section_list_list,
            section_records
        )
    else:
        raise ValueError(f"Unknown mode {args.mode}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-pd", "--plots-dir", type=str, required=True)
    parser.add_argument("-m", "--max-len", type=int, required=True)
    parser.add_argument("-d", "--debug", default=False, action="store_true", help="Debug mode")
    parser.add_argument("--mode", type=str, default="first", choices=["random", "first", "all"])
    parser.add_argument("-n", "--number", type=int, default=10)
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    plots_dir = Path(args.plots_dir)
    if not plots_dir.exists():
        parser.error(f"Plots directory {plots_dir} does not exist")
    args.plots_dir = plots_dir

    main(args)
