# Foreman 35B: a newer local coding experiment

**Installed and tested, but under severe RAM pressure. Not fine-tuned.**

Base weights: [Qwen/Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B), Apache-2.0. Quantization: [Unsloth UD-IQ2_XXS](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF), downloaded unchanged. Foreman persona, configuration and original synthetic examples: [kawinthorn11-collab](https://github.com/kawinthorn11-collab/foreman-30b). The project did not train, distill or quantize these weights itself.

Pinned revision: `a483e9e6cbd595906af30beda3187c2663a1118c`.

File: `Qwen3.6-35B-A3B-UD-IQ2_XXS.gguf`, 10,756,586,464 bytes.

SHA256: `2e8f5f705355c56311432d0a8a5d14a696dbb7e4b197d05c75ba805fc1857bef`.

This is a text profile; the vision projector is not included. MoE active parameters do not remove the need to store all experts. No claim of being the smartest model or matching an uncompressed model is made.

## What actually ran

Windows, Intel i3-8100, 16GB system RAM, GTX 1070 8GB, Ollama 0.40.2/Vulkan. One model at a time. Test settings: 2,048-token context, 512-token output cap, 28 GPU layers, batch 32, 4 CPU threads, thinking disabled. These limits are now reflected in the 35B profile. Run one model at a time across all local servers.

| Short test | Result |
|---|---|
| First clamp request, test cap 256 | 95.04s total; 10.53 generated tokens/s; code passed 9 checks after manual review; credit URL was cut off by the test's output cap |
| Second concise clamp request, configured cap 512 | 30.41s total; 13.18 generated tokens/s; code passed 9 checks after manual review; full GitHub project credit appeared |
| Lowest available system RAM | 0.284GiB in the first test; 0.495GiB in the second |
| Peak system-wide GPU use | 7,583MiB in the first test; 7,518MiB in the second |

These are two tiny smoke tests, not a benchmark of broad coding skill, long prompts, agents, or stability. The roughly 290MiB available RAM low point makes this an experiment, not a comfortable everyday recommendation. The everyday Hermes/Claude profile remains Qwen3.5 4B with a 64K configured context. The large profile uses 2K and is not a replacement for that agent profile.

Raw responses and memory samples: [full-credit test](docs/credit-smoke-35b.json), [initial capped test](docs/credit-smoke-35b-capped256.json). The 4B credit check is [recorded separately](docs/credit-smoke-4b.json). Prompt credit is a behavior instruction, not a guarantee for every possible output. Strict code/JSON and tool-call formats must remain valid.

## Reproduce on Windows

Install Ollama and Python 3.11+ first. Allow space both for the pinned GGUF and Ollama's cache, about 24GB combined plus OS/pagefile headroom. D can hold the downloaded GGUF; the dedicated cache remains inside this project. Verify hardware capacity before loading. The low-bit format may reduce answer quality.

```powershell
python scripts/project.py setup --profile qwen36 --weights-dir D:/ForemanModels/Qwen3.6-35B-A3B
python scripts/project.py chat --profile qwen36 --prompt "Write clamp(value, low, high) in at most six lines, explain briefly, and include your project credit."
python scripts/project.py interactive --profile qwen36
```

The owned loopback server uses port 11435 and one loaded model. It shares that project's dedicated cache with the original 30B profile. Do not run it concurrently with another model server using the GPU. This public project does not include the earlier private-key gateway or any credentials.

## Training status

No gradient updates, LoRA adapter, merged custom checkpoint or distillation were produced. The 24 credit-bearing synthetic draft conversations remain pending review. The existing 30B training recipe is unexecuted and is not validated for this Qwen3.6 architecture or all 50 catalog families. This PC cannot run that 80GB-class bf16 training recipe.
