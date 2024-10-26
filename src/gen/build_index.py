import argparse
import logging
import time
from pathlib import Path
from gen.index_builder import IndexBuilder
from gen.element_dumper import ElementDumper
from gen.element_validator import ElementValidator
from plumbing.queued_handler import QueuedHandler, JsonQueuedHandler, \
    BatchedQueuedHandler, JBQueuedHandler


logger = logging.getLogger(__name__)


def main(args):
    # Chain: builder -> chainable_builder -> validator -> chainable_validator -> dumper

    choice = 3
    if choice == 1:
        queued_handler_class = JsonQueuedHandler
    elif choice == 2:
        queued_handler_class = BatchedQueuedHandler
    elif choice == 3:
        queued_handler_class = JBQueuedHandler
    else:
        queued_handler_class = QueuedHandler

    builder: IndexBuilder = IndexBuilder(args)
    if args.mode == "queued":
        chainable_builder = queued_handler_class("builder -> validator")
        builder.chain(chainable_builder)
    else:
        chainable_builder = builder

    validator: ElementValidator = ElementValidator(args)
    chainable_builder.chain(validator)

    if args.mode == "queued":
        chainable_validator = queued_handler_class("validator -> dumper")
        validator.chain(chainable_validator)
    else:
        chainable_validator = validator

    dumper: ElementDumper = ElementDumper()
    chainable_validator.chain(dumper)

    if args.mode == "queued":
        getattr(chainable_builder, 'start', lambda: None)()
        getattr(chainable_validator, 'start', lambda: None)()

    builder.build()

    if args.mode == "queued":
        getattr(chainable_builder, 'stop', lambda: None)()
        getattr(chainable_validator, 'stop', lambda: None)()

    article_count = len(builder.articles)
    paragraph_count = sum(len(article._paragraphs) for article in builder.articles)
    print(f"Done. {article_count} articles, {paragraph_count} paragraphs")


if __name__ == '__main__':
    t0 = time.time()

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Show random paragraphs from a JSON file.")
    parser.add_argument("-t", "--text", type=str, help="Path to the text file")
    parser.add_argument("-pp", "--path-prefix", type=str, help="Prefix of element files")
    parser.add_argument("-m", "--max-len", type=int, help="Maximum segment length")
    parser.add_argument("-d", "--debug", default=False, action="store_true", help="Debug mode")
    parser.add_argument("--mode", type=str, choices=["inline", "queued", "queued_threaded"],
                        help="Mode: inline, queued, queued_threaded")
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

    if args.mode is None:
        parser.error("Please provide the mode")

    main(args)
    logger.info(f"Elapsed time: {time.time() - t0:.2f} seconds")
