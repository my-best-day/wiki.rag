import logging
import argparse
import numpy as np
from pathlib import Path
from gen.embedding_utils import EmbeddingUtils, TargetStype

logger = logging.getLogger(__name__)


def quantize_embeddings(
        input_file: str,
        output_file: str,
        dim: int,
        stype: TargetStype,
        l2_normalized: bool,
        l2_verify: bool) -> None:

    logger.info("Morphing embeddings with in file: %s, out file: %s, dim: %s, stype: %s",
                input_file, output_file, dim, stype)

    data = np.load(input_file)
    embeddings = data["embeddings"]

    if l2_verify:
        if not EmbeddingUtils.are_l2_normalized(embeddings):
            raise ValueError("Embeddings are not L2 normalized")
        l2_normalized = True

    morphed_embeddings = EmbeddingUtils.morph_embeddings(embeddings, dim, l2_normalized, stype)

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
                        help='Source dimension')
    parser.add_argument('-d', '--dim', type=int, choices=[768, 512, 256, 128, 64],
                        help='Target dimension')
    parser.add_argument('-m', '--max-len', type=int, help='Max length')
    parser.add_argument('-s', '--stype', type=str, help='Stype'
                        , choices=["float32", "float16", "int8", "uint8"])
    parser.add_argument('-f', '--force', action='store_true', help='Force overwrite')
    parser.add_argument('--l2-normalized', action='store_true', default=False,
                        help='Is embedding normalized')
    parser.add_argument('--l2-verify', action='store_true', default=False,
                        help='Verify embedding is L2 normalized')
    args = parser.parse_args()

    if args.input_file is None or args.output_file is None:
        if args.prefix is None or \
            args.max_len is None or \
                args.src_dim is None or args.dim is None:

            raise ValueError("Either files or (prefix, max_len, source_dim, dim) must be provided")

    if args.input_file is None:
        args.input_file = f"{args.prefix}_{args.max_len}_{args.src_dim}_embeddings.npz"

    if args.output_file is None:
        stype_part = f"_{args.stype}" if args.stype != "float32" else ""
        args.output_file = f"{args.prefix}_{args.max_len}_{args.dim}{stype_part}_embeddings.npz"

    if not Path(args.input_file).exists():
        parser.error(f"Input file {args.input_file} does not exist")

    if Path(args.output_file).exists() and not args.force:
        parser.error(f"Output file {args.output_file} already exists (use -f to force overwrite)")

    if not args.l2_normalized and not args.l2_verify:
        parser.error("Quantization only supported for L2 normalized embeddings")

    quantize_embeddings(
        args.input_file,
        args.output_file,
        args.dim,
        args.stype,
        args.l2_normalized,
        args.l2_verify)
