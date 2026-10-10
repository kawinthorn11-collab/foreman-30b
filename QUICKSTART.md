# Try Foreman in three steps

Foreman is an English-speaking local coding experiment based on Qwen3-Coder-30B-A3B-Instruct. This preview customizes the system prompt; it does not contain newly trained weights.

## Before downloading

- Windows PC, Python 3.11+, [Ollama](https://ollama.com/download/windows), and a GPU/driver supporting Vulkan.
- About 26GB free disk for the pinned GGUF and a separate Ollama model cache. The source ZIP does not include these weights.
- The reference 16GB RAM / GTX 1070 PC completed short requests, but available RAM fell to 32MiB. This is **not a comfortable minimum specification**. More free RAM is preferable. Keep other model/GPU workloads closed.
- Initial context is 2,048 tokens. Do not assume 64k context fits this machine.

## 1. Download and extract

Get [Foreman-30B-v0.1.0-preview.zip](https://github.com/kawinthorn11-collab/foreman-30b/releases/download/v0.1.0-preview/Foreman-30B-v0.1.0-preview.zip) from the [preview release](https://github.com/kawinthorn11-collab/foreman-30b/releases/tag/v0.1.0-preview). Extract it to a normal local folder. Windows cannot run the project correctly from inside the ZIP viewer.

## 2. Prepare the model

Open PowerShell in the extracted folder:

```powershell
python scripts/project.py setup
```

This downloads approximately 11.8GB, verifies SHA256, starts a dedicated loopback Ollama server, and imports the Foreman model. The download is from the public upstream publisher. An interrupted download can resume. Expect a substantial first-run download and import.

## 3. Ask a small coding question

```powershell
python scripts/project.py chat --prompt "Explain when to use a set instead of a list."
```

For interactive chat, double-click `Start-Foreman.cmd` after setup. On the author's PC, the existing Foreman desktop shortcut opens UTF-8 Windows Terminal. On other PCs, a terminal/font supporting your language may be needed.

## Troubleshooting

| Symptom | Action |
|---|---|
| Python or Ollama not found | Install the prerequisites, reopen the terminal, or set `FOREMAN_OLLAMA` to the executable path. |
| Port occupied by an unowned server | Choose a free port in `config.json`. The project refuses to import into another server. |
| Very slow first answer | Model loading and prompt evaluation add delay. The measured cold request was 107.72 seconds; generation speed alone is not total response time. |
| RAM/VRAM full | Stop the model workload and reduce other memory use. More RAM may be necessary. Lowering GPU layers increases CPU/RAM use; it is not a universal fix. |
| SHA256 mismatch | Do not use the model file. Keep the configured pinned source/hash; redownload rather than bypassing verification. |

Generated code needs review. The two smoke functions passing 13 checks does not establish broad coding proficiency. See [raw results](docs/benchmark.json) and the [model card](MODEL_CARD.md).
