# Foreman Local50: one older PC, fifty choices

Local50 replaces the oversized catalog idea with **50 distinct, smaller upstream weight sets**. Each selected model receives the shared Foreman English coding persona and GitHub credit policy. These are prompt profiles, not fifty training runs or newly created weights.

The [reviewed registry](local50-models.json) lists exact Ollama tags, weight SHA256 fingerprints, download sizes, source pages and license sources. Fifty main candidates total **154,269,328,269 bytes (143.675 GiB)** before shared-layer savings. Ten additional, distinct reserves allow a model that fails on the target machine to be replaced. Metadata verification is separate from successful local inference.

## Install and actually test

Use current [Ollama for Windows](https://ollama.com/download/windows), Python 3.11+, a GPU driver with Vulkan support and **at least 190 GiB free disk space for a new main-candidate cache**. Reserve candidates or failed partial downloads can require additional space. The original machine has 16GB RAM and a GTX 1070 with 8GB VRAM. Model weights live on D; models run one at a time.

In one PowerShell terminal, start a dedicated loopback server. Stop another server on this port first, or use a free port in both commands. Environment variables affect the server process, not an already-running Ollama tray application.

```powershell
$env:OLLAMA_HOST = '127.0.0.1:11436'
$env:OLLAMA_MODELS = 'D:/ForemanModels/OllamaModels'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$env:OLLAMA_NUM_PARALLEL = '1'
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_VULKAN = '1'
$env:CUDA_VISIBLE_DEVICES = '-1'
New-Item -ItemType Directory -Force $env:OLLAMA_MODELS | Out-Null
ollama serve
```

From this project directory, in a second terminal:

```powershell
python scripts/local_collection.py --cache D:/ForemanModels/OllamaModels --ollama "C:/Users/YOUR_USER/AppData/Local/Programs/Ollama/ollama.exe" --port 11436 --direct-download
```

Replace the executable path with your real Ollama installation. The original private desktop installation uses port11434, while the public example uses11436 to avoid its other services.

The installer pulls one base, compares its installed model-layer digests with the reviewed registry, creates a `foreman-...:latest` profile, runs a real request, then unloads it. The optional direct-download transport first resumes an official blob stream, with a 30-minute budget checked between bounded socket reads. A read may finish up to its 12-second inactivity timeout after that deadline. If streaming fails, bounded HTTP ranges provide a fallback. Exact ranges and the final blob's size/SHA256 are verified before Ollama imports the original metadata. Slow intervals are repartitioned on retry; partial streams and range segments can resume. Successful range fallback removes its redundant stream partial. Initial collection limits are **2,048 context tokens / 512 output tokens** with four CPU threads and a batch size of 64. These conservative settings are separate from the existing 4B agent's 64K profile. Larger native context support does not mean it fits this machine's RAM/VRAM.

Progress and outputs are stored in ignored `collection-local/progress.json` and `collection-local/verified-models.json`. Re-running validates the actual profile's weight identity and skips successful installed profiles, while partial Ollama downloads resume. Add `--skip-failed` to try reserves instead of retrying failures already recorded during a previous run. A single installer lock prevents two simultaneous runs. After a crash, verify the PID recorded in `collection-local/installer.lock` is no longer running before removing that stale lock and restarting the same command. Do not delete model blobs to resume.

Only nonempty successful responses count as usable profiles. Runtime failures are recorded and reserves are tried until50 distinct weights answer, or all reviewed candidates are exhausted. Missing/changed weight manifests are not counted. Before each candidate, the installer requires free space for three copies of its download size plus a20GiB reserve, covering a retained stream, range parts and assembly. It does not delete existing models or alter their weights.

## Choose a model

After installation, select a successful profile from `collection-local/verified-models.json`:

```powershell
$env:OLLAMA_HOST = '127.0.0.1:11436'
ollama run foreman-qwen3.5-4b:latest --think=false
```

Or call its native local API:

```powershell
$body = @{model='foreman-qwen3.5-4b:latest'; stream=$false; think=$false; keep_alive=0; messages=@(@{role='user';content='Explain this Python function.'})} | ConvertTo-Json -Depth 10
Invoke-RestMethod http://127.0.0.1:11436/api/chat -Method Post -ContentType application/json -Body $body
```

This Ollama endpoint is loopback-only and unauthenticated. The original PC's separate desktop gateway at8787 uses its private Bearer API key. That key, client settings and installed runtimes are excluded from this repository and release ZIP.

The desktop's model selector is populated from verified installed profiles. Hermes Agent and Claude Code keep the existing tool-capable4B default. A model being able to chat does not establish compatibility with an agent's tools, context requirements or protocols; check recorded capabilities before using a different model in a tool client.

## Read the evidence honestly

Each smoke record contains the actual answer, timings, token rate, sampled available system RAM, credit compliance and a separate coding check. The prompt asks for a short `is_even(n)` function. A strict arithmetic-only Python AST allowlist precedes six checks; calls, imports, attributes, loops and decorators are rejected. Other generated code is never executed by this installer.

A nonempty answer is an inference smoke pass, **not a coding-quality benchmark**. A model can pass inference while failing the code or credit check. Sampling available system RAM does not measure peak VRAM or prove stability under longer workloads. Reasoning models may use their output budget for thinking and fail the visible-answer test; those failures remain in the report rather than being advertised as working.

## Credit and licenses

Normal Foreman replies are instructed to include:

> Foreman customization by kawinthorn11-collab — https://github.com/kawinthorn11-collab/foreman-30b

Prompt compliance varies. Strict JSON/code-only and tool protocols retain their valid format. The credit covers the persona/configuration and original style examples; upstream weights retain their original authors and licenses. License links are recorded per model, including Gemma, Llama, Falcon and DeepSeek terms. Free local downloads are not permission to ignore upstream terms.

The 30B/35B low-bit experiments remain separate historical profiles. Their earlier results and RAM limitations are preserved in the existing reports. No fifty-model fine-tuning, distillation or merged adapters have been performed.
