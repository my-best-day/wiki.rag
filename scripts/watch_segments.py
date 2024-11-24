import time
import logging
import argparse
from pathlib import Path
from gen.element.store import Store
from gen.element.element import Element
from gen.element.segment import Segment
from gen.element.extended_segment import ExtendedSegment

__import__("gen.element.article")
__import__("gen.element.extended_segment")
__import__("gen.element.fragment")
__import__("gen.element.list_container")


logger = logging.getLogger(__name__)


def main(args):
    store = Store()
    text_path = Path(args.text)
    segment_path = Path(f"{args.path_prefix}_{args.max_len}_segments.json")
    store.load_elements(text_path, segment_path)
    print(f"loaded {len(Element.instances)} elements")
    # count elements that are instanceof Segment
    segments = [element for element in Element.instances.values()
                if isinstance(element, Segment)]
    print(f"found {len(segments)} segments")
    extended_segments = [element for element in Element.instances.values()
                         if isinstance(element, ExtendedSegment)]
    print(f"found {len(extended_segments)} extended segments")


if __name__ == '__main__':
    t0 = time.time()

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Show random paragraphs from a JSON file.")
    parser.add_argument("-t", "--text", type=str, help="Path to the text file")
    parser.add_argument("-pp", "--path-prefix", type=str, help="Prefix of element files")
    parser.add_argument("-m", "--max-len", type=int, help="Maximum segment length")
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

    main(args)
    logger.info(f"Elapsed time: {time.time() - t0:.2f} seconds")
