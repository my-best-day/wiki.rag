import time
import numpy as np
import torch.nn.functional as F
import torch
import logging

logger = logging.getLogger(__name__)


def gpu_process_embeddings(
        input_file: str,
        output_file: str,
        target_dim: int,
        batch_size: int) -> None:
    """
    Process embeddings using GPU for normalization and dimension reduction.

    Args:
        input_file (str): Path to the input file containing embeddings.
        output_file (str): Path to the output file to save processed embeddings.
        target_dim (int): Target dimension for the embeddings.
        batch_size (int): Batch size for processing.
    """
    logger.info(f"Starting processing with input file: {input_file}, output file: {output_file}, target dim: {target_dim}, batch size: {batch_size}")

    # Load existing embeddings
    data = np.load(input_file)
    embeddings = data['embeddings']

    if target_dim > embeddings.shape[1]:
        raise ValueError(f"Target dimension {target_dim} exceeds input dimension {embeddings.shape[1]}")

    # Determine device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Prepare output array
    processed_embeddings = []

    count = len(embeddings)
    batch_count = count // batch_size + 1
    elapsed_list = []
    # Process in batches
    for i in range(0, len(embeddings), batch_size):
        t0 = time.time()
        # Get batch
        batch = embeddings[i:i + batch_size]

        # Convert to GPU tensor
        tensor_batch = torch.from_numpy(batch).to(device)

        # Layer normalization
        normalized_batch = F.layer_norm(tensor_batch,
                                        normalized_shape=(tensor_batch.shape[1],))

        # Dimension reduction
        reduced_batch = normalized_batch[:, :target_dim]

        # L2 Normalization
        final_batch = F.normalize(reduced_batch, p=2, dim=1)

        # Move back to CPU and append
        processed_embeddings.append(final_batch.cpu().numpy())
        elapsed = time.time() - t0
        elapsed_list.append(elapsed)
        if len(elapsed_list) % 100 == 0:
            processed_batch = i // batch_size + 1
            logger.info("Processed %s / %s batches. "
                        "Time per batch: %.2f s",
                        processed_batch, batch_count, np.mean(elapsed_list))
            elapsed_list.clear()

    # Concatenate processed batches
    final_embeddings = np.concatenate(processed_embeddings)

    # Save processed embeddings
    np.savez(output_file,
             uids=data['uids'],
             embeddings=final_embeddings)


def main(args):
    gpu_process_embeddings(
        args.input_file,
        args.output_file,
        args.dim,
        args.batch_size
    )


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    import argparse

    parser = argparse.ArgumentParser(description='Reduce embedding dimension')
    parser.add_argument('-i', '--input-file', type=str, help='Input file',
                        required=True)
    parser.add_argument('-o', '--output_file', type=str, help='Output file',
                        required=True)
    parser.add_argument('-d', '--dim', type=int, choices=[512, 256, 128, 64],
                        help='Target dimension', required=True)
    parser.add_argument('-bs', '--batch_size', type=int, help='Batch size',
                        required=True)

    args = parser.parse_args()

    if args.batch_size <= 0:
        raise ValueError("Batch size must be positive.")

    main(args)

