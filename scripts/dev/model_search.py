import time
from huggingface_hub import HfApi

# Initialize API
api = HfApi()
print("API initialized")

# Get all sentence-transformer models
models = api.list_models(filter="sentence-transformers", language="en")
# print(f"Found {len(models)} sentence-transformer models")

# Filter based on custom criteria (e.g., parameters, sequence length)
# filtered_models = []
t0 = time.time()
seq_lengths = []
pars = []
has_meta = 0
for i, model in enumerate(models):
    elapsed = time.time() - t0
    if (i + 1) % 100 == 0 or elapsed > 60:
        print(
            f"Processing model {i + 1}: {model.modelId} in {elapsed:.2f} seconds; "
            f"meta: {has_meta}, ", end=""
        )
        if has_meta > 0:
            print(
                f"avg p: {sum(pars) / has_meta}, min p: {min(pars)}, max p: {max(pars)}, "
                f"avg l: {sum(seq_lengths) / has_meta}, min l: {min(seq_lengths)}, "
                f"max l: {max(seq_lengths)}"
            )
        else:
            print()

        t0 = time.time()
    model_info = api.model_info(model.modelId)
    if model_info.config:
        params = model_info.config.get("num_parameters")
        seq_length = model_info.config.get("max_position_embeddings")
        if params and seq_length:
            has_meta += 1
            pars.append(params)
            seq_lengths.append(seq_length)
            if params < 130_000_000 and seq_length >= 500:  # Example criteria
                # filtered_models.append((model.modelId, params, seq_length))
                print(f"Model {model.modelId}, params: {params}, seq_length: {seq_length}")

# Print filtered models
# print(filtered_models)
