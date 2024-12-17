#!/usr/bin/env python

import logging
import argparse
import numpy as np
from pathlib import Path
from gen.embedding_store import EmbeddingStore
from gen.embedding_utils import EmbeddingUtils, TargetStype, EmbeddingConfig

logger = logging.getLogger(__name__)


def quantize_embeddings(
        input_file: str,
        output_file: str,
        dim: int,
        stype: TargetStype,
        l2_normalize: bool,
        norm_type: TargetStype,
        l2_verify: bool) -> None:

    logger.info("Morphing embeddings with in file: %s, out file: %s, dim: %s, stype: %s",
                input_file, output_file, dim, stype)

    data = np.load(input_file)
    embeddings = data["embeddings"]

    if l2_verify:
        if not EmbeddingUtils.are_l2_normalized(embeddings):
            raise ValueError("Embeddings are not L2 normalized")
        l2_normalize = False

    morphed_embeddings = EmbeddingUtils.morph_embeddings(
        embeddings, dim, l2_normalize, norm_type, stype)

    np.savez(output_file,
             uids=data['uids'],
             embeddings=morphed_embeddings)

    logger.info("Quantized embeddings saved to %s", output_file)


if __name__ == "__main__":
    # python quantize_embeddings.py -i data/test_5000_512.npz -o data/test_5000_512_int8.npz -s int8
    # python quantize_embeddings.py -pp data_test -d 512 -m 5000 -s int8
    # -i and -o overrides -pp
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description='Quantize embeddings',
        epilog='''Example usage:
  python quantize_embeddings.py -i data/test_256_512.npz -o data/test_256_512_int8.npz -s int8
  python quantize_embeddings.py -pp data_test -d 512 -m 5000 -s int8
  -i and -o overrides -pp''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-i', '--input-file', type=str, help='Input file')
    parser.add_argument('-o', '--output-file', type=str, help='Output file')
    parser.add_argument('-pp', '--prefix', type=str, help='Prefix')
    parser.add_argument('-sd', '--src-dim', type=int, choices=[768, 512, 256, 128, 64],
                        help='Source dimension (default: target dimension)')
    parser.add_argument('-d', '--dim', type=int, choices=[768, 512, 256, 128, 64],
                        help='Target dimension')
    parser.add_argument('-m', '--max-len', type=int, help='Max length')
    parser.add_argument('-s', '--stype', type=str, help='Stype'
                        , choices=["float32", "float16", "int8", "uint8"])
    parser.add_argument('--src-stype', type=str, help='Source stype'
                        , choices=["float32", "float16", "int8", "uint8"])
    parser.add_argument('-f', '--force', action='store_true', help='Force overwrite')
    parser.add_argument('--l2-normalize', action='store_true', default=False,
                        help='l2 normalize the embeddings')
    parser.add_argument('--norm-type', type=str, choices=["float32", "float16", "int8", "uint8"],
                        help='Data type to use for L2 normalization (default: input type)')
    parser.add_argument('--src-norm-type', type=str, choices=["float32",
                        "float16", "int8", "uint8"], default=None,
                        help='Indicate the norm type of the source embeddings')
    parser.add_argument('--l2-verify', action='store_true', default=False,
                        help='Verify embedding is L2 normalized')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Enable debug logging')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.input_file is None or args.output_file is None:
        if args.prefix is None or \
            args.max_len is None or \
                args.dim is None:

            raise ValueError("Either files or (prefix, max_len, dim) must be provided")

    if args.src_dim is None:
        args.src_dim = args.dim

    if args.src_stype is None:
        args.src_stype = args.stype

    if args.src_norm_type is None:
        args.src_norm_type = args.norm_type

    if args.input_file is None:
        input_config = EmbeddingConfig(
            prefix=args.prefix,
            max_len=args.max_len,
            dim=args.src_dim,
            stype=args.src_stype,
            norm_type=args.src_norm_type
        )
        args.input_file = EmbeddingStore.get_store_path(input_config)

    if args.output_file is None:
        output_config = EmbeddingConfig(
            prefix=args.prefix,
            max_len=args.max_len,
            dim=args.dim,
            stype=args.stype,
            norm_type=args.norm_type
        )
        args.output_file = EmbeddingStore.get_store_path(output_config)

    if not Path(args.input_file).exists():
        parser.error(f"Input file {args.input_file} does not exist")

    if Path(args.output_file).exists() and not args.force:
        parser.error(f"Output file {args.output_file} already exists (use -f to force overwrite)")

    quantize_embeddings(
        args.input_file,
        args.output_file,
        args.dim,
        args.stype,
        args.l2_normalize,
        args.norm_type,
        args.l2_verify)
