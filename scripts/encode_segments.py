import time
import logging
import argparse
import numpy as np
from uuid import UUID
from pathlib import Path
from typing import List

from gen import embedding_store
from gen.encoder import Encoder
from gen.embedding_store import EmbeddingStore, EmbeddingConfig

from gen.element.store import Store
from gen.element.element import Element
from gen.element.extended_segment import ExtendedSegment

__import__("gen.element.article")
__import__("gen.element.extended_segment")
__import__("gen.element.fragment")
__import__("gen.element.list_container")


logger = logging.getLogger(__name__)


class SegmentEncoder:

    def __init__(self, args):
        self.args = args
        self.encoder = Encoder(batch_size=args.batch_size)
        self.config = EmbeddingConfig(prefix=args.path_prefix, max_len=args.max_len)
        embedding_store_path = embedding_store.get_store_path(self.config)
        self.embedding_store = EmbeddingStore(embedding_store_path, allow_empty=True)
        if not args.incremental and self.embedding_store.does_store_exist():
            self.embedding_store.delete()

    @property
    def extended_segments(self):
        store = Store()
        text_file_path = Path(args.text)
        segment_file_path = Path(f"{args.path_prefix}_{args.max_len}_segments.json")
        store.load_elements(text_file_path, segment_file_path)
        extended_segments = [element for element in Element.instances.values()
                             if isinstance(element, ExtendedSegment)]
        return extended_segments

    @property
    def extended_segments_to_encode(self):
        assert self.args.max_items >= 0, "max_items must be non-negative"

        all_extended_segments = self.extended_segments

        count = 0
        if self.args.incremental:
            count = self.embedding_store.get_count(allow_empty=True)
            extended_segments = all_extended_segments[count:]
        else:
            extended_segments = all_extended_segments

        if self.args.max_items > 0:
            extended_segments = extended_segments[:self.args.max_items]

        msg = (
            f"{len(all_extended_segments)} total ext segments, {count} processed, "
            f"{len(extended_segments)} pending"
        )
        logger.info(msg)

        return extended_segments

    def encode_segments(self):
        extended_segments = self.extended_segments_to_encode
        if not extended_segments:
            logger.info("No segments to encode")
            return

        batch_size = self.args.batch_size
        buffer_length = self.args.buffer_length
        uids_buffer = []
        embedding_buffer = []
        for i in range(0, len(extended_segments), batch_size):
            batch = extended_segments[i:i + batch_size]
            batch_text = [segment.text for segment in batch]
            batch_uids = [segment.uid for segment in batch]
            batch_embeddings = self.encode_search_sentences(batch_text)
            uids_buffer.extend(batch_uids)
            embedding_buffer.extend(batch_embeddings)
            if len(uids_buffer) >= buffer_length:
                self.persist_embeddings(uids_buffer, embedding_buffer)
                uids_buffer.clear()
                embedding_buffer.clear()

            # Process the batch here
            current_batch = i // batch_size + 1
            total_batches = (len(extended_segments) + batch_size - 1) // batch_size
            logger.info(f"Processing batch {current_batch} / {total_batches}")

        if uids_buffer:
            self.persist_embeddings(uids_buffer, embedding_buffer)

    def encode_search_sentences(self, sentences):
        # prepend "search_document: " to each sentence
        sentences = [f"search_document: {sentence}" for sentence in sentences]
        result = self.encoder.encode(sentences)
        return result

    def persist_embeddings(self, uids: List[UUID], embeddings: List[np.ndarray]) -> None:
        self.embedding_store.extend_embeddings(uids, embeddings)


def main(args):
    segment_encoder = SegmentEncoder(args)
    segment_encoder.encode_segments()


if __name__ == '__main__':
    t0 = time.time()

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Show random paragraphs from a JSON file.")
    parser.add_argument("-t", "--text", type=str, help="Path to the text file")
    parser.add_argument("-pp", "--path-prefix", type=str, help="Prefix of element files")
    parser.add_argument("-m", "--max-len", type=int, help="Maximum segment length")
    parser.add_argument("-bs", "--batch-size", type=int, help="Batch size")
    parser.add_argument("-bl", "--buffer-length", type=int, help="Buffer length")
    parser.add_argument("-i", "--incremental", default=False, action="store_true",
                        help="Incremental mode")
    parser.add_argument("-mi", "--max-items", type=int, default=0,
                        help="Maximum number of items to process (zero means no limit)")
    parser.add_argument("-d", "--debug", default=False, action="store_true", help="Debug mode")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.text is None:
        parser.error("Please provide the path to the text file")
    if args.text != "stdin":
        text = Path(args.text)
        if not text.exists():
            parser.error(f"File {args.text} not found")

    if args.path_prefix is None:
        parser.error("Please provide the path prefix")

    if args.max_len is None:
        parser.error("Please provide the maximum segment length")

    if args.batch_size is None:
        parser.error("Please provide the batch size")

    if args.buffer_length is None:
        parser.error("Please provide the buffer length")

    if args.max_items < 0:
        parser.error("max_items must be non-negative (zero means no limit)")

    main(args)
    logger.info(f"Elapsed time: {time.time() - t0:.2f} seconds")
