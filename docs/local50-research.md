# Local50 registry research

Verified 2026-10-11 UTC against public official Ollama pages and registry metadata. Exactly 50 main models and 10 optional reserves. No model weights were downloaded, no inference ran, and no runtime configuration changed.

## Byte budget and identity

The main 50 have **154,269,328,269 bytes** of additive download budget (**154.269 GB decimal; 143.675 GiB**). Their language-model layers total 148,463,745,952 bytes. The largest main model layer is 6,022,221,312 bytes, Ministral 3 8B. Additional projector/draft weights and small config/template/license layers are included in each total. Shared blobs can lower physical disk usage; filesystem/manifest overhead and temporary download space are additional. A practical main-cache allowance is at least 190 GiB, including download fallback space and the installer reserve. Reserve candidates and failed partial downloads can require more. This is a storage budget, not a peak RAM/VRAM measurement.

The ten reserves are replacement choices and are not part of the promised 50. Their separate byte sum is recorded in the JSON.

A weight fingerprint is the sorted set of `application/vnd.ollama.image.model` layer digests only. All 50 main fingerprints are distinct; all 60 including reserves are distinct. Projectors, draft models, licenses, templates, or changed aliases do not create a new counted model. One quantization is selected per training/size/architecture identity. Registry digest headers were absent; the JSON separately records SHA-256 computed over each exact manifest response body and does not present it as a server header.

The three 4B Qwen3 choices are the original April 2025 training, July 2507 instruct training, and July 2507 thinking training. They have different model digests. Current `qwen3:4b` aliases the July thinking model and is excluded. See [official Qwen3 tags](https://ollama.com/library/qwen3/tags) and the [April 29, 2025 release](https://qwenlm.github.io/blog/qwen3/). Dense and hybrid Granite4 variants have distinct architectures and model layers; tiny-H is about 6.9B packaged total, with roughly 1B active. See [Granite4](https://ollama.com/library/granite4).

The research-license-only `qwen2.5:3b` and `qwen2.5-coder:3b` entries were replaced with Apache-2.0 `granite3.2:2b` and `granite3.2:8b`. Granite3.2 and Granite3.3 are distinct fine-tuned releases and have distinct model digests; they are not alternate quantizations of one release. The official [Granite3.2 page](https://ollama.com/library/granite3.2) dates that release to February 26, 2025.

## Main 50

GB means decimal downloaded bytes, not peak RAM/VRAM. Parameters are approximate packaged GGUF values from registry config; effective/model-family labels can differ. Age is the official registry page display observed 2026-10-11, not an invented exact release date. Older rows are retained as reference releases rather than advertised as new 2026 models. Each row links its actual official tag page; the JSON links its verified public manifest and exact bundled license blob.

| # | Exact tag and official source | Packaged parameters | Download GB | License | Registry age observed |
|---:|---|---|---:|---|---|
| 1 | [qwen3.5:0.8b](https://ollama.com/library/qwen3.5:0.8b) | 752.39M | 1.322 | Apache-2.0 | 6 days ago |
| 2 | [qwen3.5:2b](https://ollama.com/library/qwen3.5:2b) | 1.9B | 2.683 | Apache-2.0 | 6 days ago |
| 3 | [qwen3.5:4b](https://ollama.com/library/qwen3.5:4b) | 4.2B | 3.324 | Apache-2.0 | 6 days ago |
| 4 | [qwen3.5:9b](https://ollama.com/library/qwen3.5:9b) | 9.0B | 6.551 | Apache-2.0 | 6 days ago |
| 5 | [qwen3:0.6b](https://ollama.com/library/qwen3:0.6b) | 751.63M | 0.523 | Apache-2.0 | 1 year ago |
| 6 | [qwen3:1.7b](https://ollama.com/library/qwen3:1.7b) | 2.0B | 1.359 | Apache-2.0 | 1 year ago |
| 7 | [qwen3:4b-q4_K_M](https://ollama.com/library/qwen3:4b-q4_K_M) | 4.0B | 2.621 | Apache-2.0 | 1 year ago |
| 8 | [qwen3:4b-instruct-2507-q4_K_M](https://ollama.com/library/qwen3:4b-instruct-2507-q4_K_M) | 4.0B | 2.497 | Apache-2.0 | 1 year ago |
| 9 | [qwen3:4b-thinking-2507-q4_K_M](https://ollama.com/library/qwen3:4b-thinking-2507-q4_K_M) | 4.0B | 2.497 | Apache-2.0 | 1 year ago |
| 10 | [qwen3:8b](https://ollama.com/library/qwen3:8b) | 8.2B | 5.225 | Apache-2.0 | 1 year ago |
| 11 | [ministral-3:3b](https://ollama.com/library/ministral-3:3b) | 3.8B | 2.954 | Apache-2.0 | 10 months ago |
| 12 | [ministral-3:8b](https://ollama.com/library/ministral-3:8b) | 8.9B | 6.022 | Apache-2.0 | 10 months ago |
| 13 | [gemma4:e2b](https://ollama.com/library/gemma4:e2b) | 4.6B | 4.587 | Apache-2.0 | yesterday |
| 14 | [gemma4:e4b](https://ollama.com/library/gemma4:e4b) | 7.5B | 6.584 | Apache-2.0 | yesterday |
| 15 | [granite4:1b](https://ollama.com/library/granite4:1b) | 1.6B | 3.267 | Apache-2.0 | 11 months ago |
| 16 | [granite4:3b](https://ollama.com/library/granite4:3b) | 3.4B | 2.100 | Apache-2.0 | 11 months ago |
| 17 | [granite4:1b-h](https://ollama.com/library/granite4:1b-h) | 1.5B | 1.559 | Apache-2.0 | 11 months ago |
| 18 | [granite4:3b-h](https://ollama.com/library/granite4:3b-h) | 3.2B | 1.943 | Apache-2.0 | 11 months ago |
| 19 | [granite4:tiny-h](https://ollama.com/library/granite4:tiny-h) | 6.9B | 4.231 | Apache-2.0 | 11 months ago |
| 20 | [phi4-mini:3.8b](https://ollama.com/library/phi4-mini:3.8b) | 3.8B | 2.492 | MIT | 1 year ago |
| 21 | [phi4-mini-reasoning:3.8b](https://ollama.com/library/phi4-mini-reasoning:3.8b) | 3.8B | 3.152 | MIT | 1 year ago |
| 22 | [hermes3:3b](https://ollama.com/library/hermes3:3b) | 3.2B | 2.019 | Llama-3 community license | 1 year ago |
| 23 | [hermes3:8b](https://ollama.com/library/hermes3:8b) | 8.0B | 4.661 | Llama-3 community license | 1 year ago |
| 24 | [llama3.2:1b](https://ollama.com/library/llama3.2:1b) | 1.2B | 1.321 | Llama-3.2 community license | 2 years ago |
| 25 | [llama3.2:3b](https://ollama.com/library/llama3.2:3b) | 3.2B | 2.019 | Llama-3.2 community license | 2 years ago |
| 26 | [llama3.1:8b](https://ollama.com/library/llama3.1:8b) | 8.0B | 4.921 | Llama-3.1 community license | 1 year ago |
| 27 | [gemma3:1b](https://ollama.com/library/gemma3:1b) | 999.89M | 0.806 | Gemma terms | yesterday |
| 28 | [gemma3:4b](https://ollama.com/library/gemma3:4b) | 3.9B | 3.350 | Gemma terms | yesterday |
| 29 | [gemma2:2b](https://ollama.com/library/gemma2:2b) | 2.6B | 1.630 | Gemma terms | 2 years ago |
| 30 | [falcon3:7b](https://ollama.com/library/falcon3:7b) | 7.5B | 4.570 | Falcon3 TII Falcon License (modified Apache-based) | 1 year ago |
| 31 | [gemma3n:e2b](https://ollama.com/library/gemma3n:e2b) | 4.5B | 5.622 | Gemma terms | 1 year ago |
| 32 | [phi3:mini](https://ollama.com/library/phi3:mini) | 3.8B | 2.176 | MIT | 2 years ago |
| 33 | [phi3.5:3.8b](https://ollama.com/library/phi3.5:3.8b) | 3.8B | 2.176 | MIT | 2 years ago |
| 34 | [deepseek-r1:1.5b](https://ollama.com/library/deepseek-r1:1.5b) | 1.8B | 1.117 | MIT | 1 year ago |
| 35 | [deepseek-r1:7b](https://ollama.com/library/deepseek-r1:7b) | 7.6B | 4.683 | MIT | 1 year ago |
| 36 | [deepseek-r1:8b](https://ollama.com/library/deepseek-r1:8b) | 8.2B | 5.225 | MIT | 1 year ago |
| 37 | [deepseek-coder:1.3b](https://ollama.com/library/deepseek-coder:1.3b) | 1B | 0.776 | DeepSeek model license | 2 years ago |
| 38 | [deepseek-coder:6.7b](https://ollama.com/library/deepseek-coder:6.7b) | 7B | 3.828 | DeepSeek model license | 2 years ago |
| 39 | [qwen2.5:1.5b](https://ollama.com/library/qwen2.5:1.5b) | 1.5B | 0.986 | Apache-2.0 | 2 years ago |
| 40 | [qwen2.5:7b](https://ollama.com/library/qwen2.5:7b) | 7.6B | 4.683 | Apache-2.0 | 2 years ago |
| 41 | [qwen2.5-coder:1.5b](https://ollama.com/library/qwen2.5-coder:1.5b) | 1.5B | 0.986 | Apache-2.0 | 1 year ago |
| 42 | [qwen2.5-coder:7b](https://ollama.com/library/qwen2.5-coder:7b) | 7.6B | 4.683 | Apache-2.0 | 1 year ago |
| 43 | [qwen2-math:1.5b](https://ollama.com/library/qwen2-math:1.5b) | 1.5B | 0.935 | Apache-2.0 | 2 years ago |
| 44 | [qwen2-math:7b](https://ollama.com/library/qwen2-math:7b) | 7.6B | 4.431 | Apache-2.0 | 2 years ago |
| 45 | [granite3.3:2b](https://ollama.com/library/granite3.3:2b) | 2.5B | 1.545 | Apache-2.0 | 1 year ago |
| 46 | [granite3.3:8b](https://ollama.com/library/granite3.3:8b) | 8.2B | 4.943 | Apache-2.0 | 1 year ago |
| 47 | [smollm2:1.7b](https://ollama.com/library/smollm2:1.7b) | 1.7B | 1.820 | Apache-2.0 | 1 year ago |
| 48 | [mistral:7b](https://ollama.com/library/mistral:7b) | 7.2B | 4.373 | Apache-2.0 | 1 year ago |
| 49 | [granite3.2:2b](https://ollama.com/library/granite3.2:2b) | 2.5B | 1.545 | Apache-2.0 | 1 year ago |
| 50 | [granite3.2:8b](https://ollama.com/library/granite3.2:8b) | 8.2B | 4.943 | Apache-2.0 | 1 year ago |

## Optional reserves

| Exact tag and official source | Download GB | Use / limitations |
|---|---:|---|
| [falcon3:3b](https://ollama.com/library/falcon3:3b) | 2.006 | chat/instruct |
| [llama3:8b](https://ollama.com/library/llama3:8b) | 4.661 | chat/instruct |
| [llama2:7b](https://ollama.com/library/llama2:7b) | 3.827 | chat/instruct |
| [starcoder2:3b](https://ollama.com/library/starcoder2:3b) | 1.710 | code completion |
| [starcoder2:7b](https://ollama.com/library/starcoder2:7b) | 4.043 | code completion |
| [codegemma:2b](https://ollama.com/library/codegemma:2b) | 1.551 | code completion |
| [codegemma:7b](https://ollama.com/library/codegemma:7b) | 5.012 | coding/instruct (older reference) |
| [phi:2.7b](https://ollama.com/library/phi:2.7b) | 1.602 | text generation (older reference) |
| [qwen2.5:0.5b](https://ollama.com/library/qwen2.5:0.5b) | 0.398 | chat/instruct |
| [qwen2.5-coder:0.5b](https://ollama.com/library/qwen2.5-coder:0.5b) | 0.398 | chat/instruct |

## Material caveats

- The PC has 16 GB RAM and GTX1070 8 GB VRAM; metadata size checks establish plausibility, not successful Vulkan execution. Load one model at a time. Use modest text context initially and smoke-test each selected runner. Granite4 H/Mamba variants and new multimodal/draft packages deserve particular checks. [Ollama memory and concurrency FAQ](https://docs.ollama.com/faq) explains that context length and parallel requests increase memory demand.
- Qwen3.5 config requires Ollama 0.30.0; Gemma4 requires 0.30.9. The stated installed 0.40.2 exceeds those metadata minimums. Ministral3 officially requests 0.13.1; Phi4 Mini requests 0.5.13. Version comparison does not establish hardware performance. See [Qwen3.5](https://ollama.com/library/qwen3.5), [Gemma4](https://ollama.com/library/gemma4), [Ministral3](https://ollama.com/library/ministral-3), and [Phi4 Mini](https://ollama.com/library/phi4-mini).
- Qwen3.5 and Gemma4 are small multimodal packages used here for text; budgets include projectors/drafts. Ministral3 stores multimodal weights in its integrated model layer. Gemma3 1B is text-only despite its family vision badge; 4B includes a separate projector. Gemma3n E2B exposes Text input on the official Ollama page. Image/audio inference was not validated. See [Gemma3n](https://ollama.com/library/gemma3n) and [Gemma4 parameter table](https://ollama.com/library/gemma4).
- Public downloads need no paid API or login. Selected main models allow ordinary use under their applicable licenses. This does not make every license equivalent: Falcon3 uses the modified TII Falcon License; Llama/Hermes and older Gemma have community/model-specific terms. The exact bundled license URLs are recorded for every entry in the JSON. Both Qwen Research License-only 3B choices were excluded.
- Official Tools badges are recorded as advertised capability, not proof of tool-call accuracy. Badge absence means unverified, not necessarily incapable. Older Phi, math specialists, and completion reserves should not become default autonomous coding agents. [Qwen2 Math](https://ollama.com/library/qwen2-math) is a specialized 2024 English mathematics release with 4K context.
- Original DeepSeek-Coder sizes are older coding references. StarCoder2 and CodeGemma 2B reserves are completion-oriented; Phi2 is an older text-generation reference. Tiny 0.5B Qwen reserves are last-resort lightweight references.

## Exclusions and dated references

SmolLM3 `3b` and `latest` both returned 404 from the official library registry and its official page was unavailable, so an unofficial import was not substituted. Qwen2.5-Math 1.5B/7B official manifests also returned 404; actual `qwen2-math` tags fill the specialist slots. `granite4:7b` is not the valid tiny-H tag. Gemma2 9B reports 9.24B on its official page and is excluded under the strict 9B threshold. Gemma3n E4B weighs 7.55 GB and is excluded. Granite4 350M and Qwen2.5 0.5B are excluded from the selected 50 as weak general coding choices.

Verified family dates retained in JSON include [Qwen2.5, 2024-09-19](https://qwenlm.github.io/blog/qwen2.5/), [Qwen2 Math, 2024-08-08](https://qwenlm.github.io/blog/qwen2-math/), [Llama3.1, 2024-07-23](https://ai.meta.com/blog/meta-llama-3-1/), [Llama3.2, 2024-09-25](https://ai.meta.com/blog/llama-3-2-connect-2024-vision-edge-mobile-devices), [Granite3.2, 2025-02-26](https://ollama.com/library/granite3.2), and [Granite4, 2025-10-02](https://ollama.com/library/granite4). Dates refer to the upstream family announcement, not current mutable Ollama tag publication. For other references, the separately recorded observed registry age is the evidence; no precise upstream release date is asserted.

## Reproducible audit scope

GET `https://registry.ollama.ai/v2/library/NAME/manifests/TAG` validated each tag. GET of each small manifest config blob verified architecture, quantization, approximate parameters, and minimum-version metadata. GET of each small license blob verified license wording. GET of `https://ollama.com/library/NAME:TAG` verified the official page title and family capability badges. Only model/projector/draft digests and sizes were inspected; no such weight blob content was requested. All 60 selected/reserve exact pages and their license blobs were successfully verified.
