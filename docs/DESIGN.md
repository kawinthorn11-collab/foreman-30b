# Foreman 30B design

## User goal
Create an English-speaking coding assistant named Foreman (English for หัวหน้างาน), derived from a 30B model, test it on the owner's Windows PC with 16 GB RAM and GTX 1070 8 GB VRAM, and prepare a public GitHub project. The owner has no separate training GPU and requests a local test. Create example style conversations for the owner to review.

## Stages and truthful labels
1. Local prototype: import a pre-quantized Qwen3-Coder-30B-A3B-Instruct GGUF, add the Foreman system prompt, test memory, speed and small coding tasks. This is a prompted derivative, not a fine-tuned model.
2. Dataset draft: original synthetic English coding/style examples, explicitly marked unreviewed. Never mine private computer files or conversations automatically.
3. Future training: reviewed conversational data -> bf16 LoRA on suitable external GPU -> merged full-precision weights -> GGUF conversion -> imatrix calibration and quantization -> evaluation. Do not launch paid compute or pretend local training happened.
4. Distribution: GitHub contains code, prompt, dataset draft, model card and checksums; large model weights are downloaded from the upstream publisher and excluded from Git. A future trained model can be hosted on Hugging Face or a release store.

## Local memory target
Use Unsloth's UD-Q2_K_XL GGUF, 11,788,590,240 bytes, to leave room for Windows. Combine RAM and VRAM, one loaded model, one request at a time, 2,048 initial context, 4 CPU threads, 256-token initial output. Increase context only after measurement; do not promise Hermes/Claude's 64K context on this 30B profile. A 30.5B MoE activates 3.3B parameters per token but still needs the full expert weights in memory/storage.

Download pinned repository revision b17cb02dd882d5b6ab62fc777ad2995f19668350 and verify SHA256 3dee4686d756e8842aec638c5725666c76584edce76d71088732b52d2c5d7a45. The initial quantization was performed by Unsloth, not by this project. Quantization trades precision for memory; observed test results are not a broad coding benchmark.

## Isolation and publication
Use a separate loopback Ollama instance at 11435 and a project model cache. Reuse the already verified Ollama runtime on this PC, with Vulkan because the installed CUDA driver cannot run this runtime. Do not change drivers, close unrelated applications or replace the working 4B/9B configuration. Before loading 30B, unload idle local models to free VRAM. Record any inference-memory failure and stop instead of repeatedly stressing a PC that previously restarted unexpectedly.

Publish only after the repo contents are reviewable and a GitHub destination/account is known. No secrets, API keys, runtime binaries, model weights, private dataset files or local absolute paths enter Git. Retain upstream Apache-2.0 license and attribution; no claim of a new architecture or trained capability.
