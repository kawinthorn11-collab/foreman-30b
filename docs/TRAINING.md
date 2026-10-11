# Future reviewed-data LoRA and quantization

This is preparation, not a completed training run. The 24 examples are a review draft. They can teach style but do not substantiate improved coding capability. Expand with legally usable, verified coding conversations and keep a separate held-out evaluation suite.

Current [Unsloth MoE guidance](https://unsloth.ai/docs/basics/faster-moe) recommends bf16 LoRA, reports about 63GB VRAM for Qwen3-30B, and warns against current 4-bit BitsandBytes MoE training. Use an idle A100 80GB or comparable GPU, a suitable Linux/CUDA environment, and at least 150GiB free disk. The GTX 1070 cannot run this recipe.

1. Review every `data/style-draft.jsonl` row. Edit incorrect answers and mark approved. Remove rejected rows.
2. Follow the official [Qwen MoE notebook](https://github.com/unslothai/notebooks/blob/main/nb/Qwen3_MoE.ipynb) to install compatible PyTorch, Unsloth, Transformers and TRL versions. Dependencies are intentionally not claimed to be locked or validated here.
3. Run `python scripts/train_lora.py` for preflight. It refuses pending data, insufficient disk, missing bf16 CUDA, and less than 70GiB free VRAM. Only `--run` performs training. Check `--steps` and training cost before executing.
4. Execute `python scripts/train_lora.py --run --steps 50` for a small style experiment. The script saves an adapter and merged 16-bit weights. It is an untested template adapted from the official notebook; APIs may require updates. Record the exact environment, base model revision, data hash, run settings, seed, loss, and evaluation results before publication.
5. Compare the adapter against the unmodified base on held-out coding and style tasks. Do not use the same examples for both training and evaluation. Reject regressions. A small synthetic dataset can overfit.

## Convert only after a verified training run

Build official [llama.cpp](https://github.com/ggml-org/llama.cpp) on a machine with sufficient disk. Its current conversion and quantization tools must support the Qwen architecture. These commands are examples, not executed artifacts:

```bash
python convert_hf_to_gguf.py /path/to/merged --outfile foreman-f16.gguf --outtype f16
./llama-imatrix -m foreman-f16.gguf -f calibration.txt -o imatrix.dat
./llama-quantize --imatrix imatrix.dat foreman-f16.gguf foreman-Q2_K.gguf Q2_K
```

Use representative, legally usable calibration text, separate from evaluation examples. Follow the [quantizer README](https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md) for supported formats and flags. A standard Q2_K quantization is not identical to Unsloth's UD-Q2_K_XL dynamic recipe. Full-precision source weights alone are about 61GB; conversion needs additional storage. The current local disk and GPU are not a full training/conversion setup.

After conversion, compute SHA256, record size and runtime memory, and rerun the held-out suite at the target low-bit format. Publish weights through a suitable model host with a derivative model card, adapter/base license attribution, exact training provenance, and limitations. GitHub can link to those weights once they actually exist.

## 50-model registry and credit dataset

The catalog is not a promise of 50 trained models. The shared prompt and 24 pending synthetic examples include the project credit requested by kawinthorn11-collab. No gradient updates, adapters or merged fine-tuned checkpoints have been produced.

The existing `train_lora.py` recipe targets only Qwen3-Coder-30B-A3B-Instruct; it is not validated for Qwen3.6, DeepSeek, Kimi, Gemma, Hermes, MiniMax, GLM or Nemotron. Training/export requires architecture-specific support, compatible GPU capacity, reviewed data and compliance with each upstream license. A GTX 1070 with 8GB VRAM and a 16GB host cannot execute this 30B bf16 recipe. Downloading a GGUF or creating an Ollama profile performs neither training nor knowledge distillation.

Quantization reduces numerical precision and storage, not the number of parameters. Distilling a large teacher into a smaller student would require a separate licensed dataset, training run and evaluation; no such work is claimed here.
