import lzma
import numpy as np
import sys


def compress_embedding_file(file_name):
    base_name = file_name.split(".")[0]
    target_name = f"{base_name}_compressed.xz"

    with open(file_name, 'rb') as f_in, \
            lzma.open(target_name, 'wb') as f_out:
        f_out.write(f_in.read())


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: compress_embeddings.py <file_name>")
        sys.exit(1)
    file_name = sys.argv[1]
    compress_embedding_file(file_name)
