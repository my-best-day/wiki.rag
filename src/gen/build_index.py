import argparse
import logging
import time
from pathlib import Path
from gen.index_builder import IndexBuilder
from gen.element_dumper import ElementDumper
from gen.element_validator import ElementValidator
from plumbing.queued_handler import QueuedHandler


logger = logging.getLogger(__name__)


def main(args):
    # Chain: builder -> chainable_builder -> validator -> chainable_validator -> dumper

    builder: IndexBuilder = IndexBuilder(args)
    if args.mode == "queued":
        chainable_builder = QueuedHandler("builder -> validator")
        builder.chain(chainable_builder)
    else:
        chainable_builder = builder

    validator: ElementValidator = ElementValidator(args)
    chainable_builder.chain(validator)

    if args.mode == "queued":
        chainable_validator = QueuedHandler("validator -> dumper")
        validator.chain(chainable_validator)
    else:
        chainable_validator = validator

    dumper: ElementDumper = ElementDumper()
    chainable_validator.chain(dumper)

    if args.mode == "queued":
        chainable_builder.start()
        chainable_validator.start()

    logger.info("Sleeping...")
    time.sleep(5)
    logger.info("Building index")
    builder.build()
    logger.info("Index built")

    if args.mode == "queued":
        logger.info("Stopping queued handlers")
        # chainable_builder.stop()
        # chainable_validator.stop()


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
