# Foreman 30B model card

This card preserves the original 30B experiment. The current smaller-model collection is documented in [LOCAL50.md](LOCAL50.md), with per-model provenance and licenses in [local50-models.json](local50-models.json). Local50 uses prompt profiles, not newly trained weights; local inference status is separate from reviewed registry metadata.

**Release type:** prompted local prototype. **Training status:** not trained. No LoRA adapter or merged custom weights exist in this release.

Base: `Qwen/Qwen3-Coder-30B-A3B-Instruct`, 30.5B total / 3.3B active parameters, 48 layers. English coding style is configured by `prompt.txt`. Quantization: Unsloth's `UD-Q2_K_XL`, downloaded unchanged. This project has not performed that quantization itself.

GGUF revision: `b17cb02dd882d5b6ab62fc777ad2995f19668350`.

SHA256: `3dee4686d756e8842aec638c5725666c76584edce76d71088732b52d2c5d7a45`.

File: `Qwen3-Coder-30B-A3B-Instruct-UD-Q2_K_XL.gguf`, 11,788,590,240 bytes.

License: upstream Apache-2.0; retain attribution and license when distributing derivatives. Download URLs identify the upstream publisher. GitHub hosts project source, not multi-gigabyte weights.

Intended use: local English coding assistance and a reproducible customization experiment. Review generated code before executing or deploying it. Coding proficiency is inherited from the base model, affected by low-bit quantization, and not proven by a small smoke test. The draft style corpus is unreviewed and unused for training.

Hardware target: Windows, 16GB RAM plus GTX 1070/8GB VRAM, Vulkan, partial offload, 2,048 context. Long-context and agent workloads are outside this initial test. No general performance guarantee is made.

Local measurement: three short requests completed on this PC. Identity matched Foreman/English; two manually reviewed Python functions passed 13 checks. Generation 4.29–10.79 tokens/sec; cold request 107.72 seconds; GPU usage peaked at 7,256MiB system-wide. Available RAM dipped to 32MiB: **severe memory pressure, not comfortable daily use**. The runtime model allocation reported 6,918,714,163 bytes VRAM and 12,111,692,431 bytes total. System-wide readings include other applications. The model was unloaded after testing. The deduplicate response violated the code-only instruction by adding explanation. See `docs/benchmark.json` for raw results. This is a smoke test, not proof of excellent coding ability. Training recipe is unexecuted and its environment has not been validated on an external GPU.

## 2026-10-11 extension

The original 30B result above is retained. A separate Qwen3.6-35B IQ2_XXS experiment is documented in [FOREMAN-35B.md](FOREMAN-35B.md), with pinned provenance in config-35b.json. The registry contains 50 verified repository references, not 50 installed or trained models.

Credit applies to the Foreman persona/configuration and original synthetic style examples by kawinthorn11-collab. It does not claim ownership of Qwen or any other upstream weights. All draft examples include project credit and remain pending review. All published model profiles remain prompt customization, with no fine-tuned adapter or merged weights.
