import argparse
import logging
import time
from pathlib import Path
from gen.element.store import Store
from gen.element.element import Element
from gen.index_builder import IndexBuilder
from gen.element_validator import ElementValidator

from helpers.element_dumper import ElementDumper


logger = logging.getLogger(__name__)


def main(args):
    builder: IndexBuilder = IndexBuilder(args)

    validator: ElementValidator = ElementValidator(args)
    builder.chain(validator)

    dumper: ElementDumper = ElementDumper(False)
    validator.chain(dumper)

    builder.build()

    article_count = len(builder.articles)
    paragraph_count = sum(len(article._paragraphs) for article in builder.articles)
    print(f"Done. {article_count} articles, {paragraph_count} paragraphs")

    element_file_path = Path(args.path_prefix + "_elements.json")
    element_store = Store()
    element_store.store_elements(element_file_path, Element.instances.values())


if __name__ == '__main__':
    t0 = time.time()

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Show random paragraphs from a JSON file.")
    parser.add_argument("-t", "--text", type=str, help="Path to the text file")
    parser.add_argument("-pp", "--path-prefix", type=str, help="Prefix of element files")
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

    main(args)
    logger.info(f"Elapsed time: {time.time() - t0:.2f} seconds")
