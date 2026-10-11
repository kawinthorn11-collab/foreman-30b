# Local50 hardware snapshot: installation in progress

Snapshot UTC: 2026-10-11T15:29:44.682624+00:00

**15/50 distinct models returned visible answers** on a 16GB RAM / GTX 1070 8GB PC with Ollama 0.40.2 and Vulkan. This is a dated progress snapshot, not completion of the fifty-model collection.

The full GitHub credit appeared in 14/15 responses. The restrictive Python check passed 9/15 responses. These results are separate: a model that answers may still ignore formatting or credit instructions. No fine-tuning or new weights were produced.

All requests used 2,048 context tokens / 512 output tokens, four threads, batch64, one loaded model, and unload after inference. Minimum available RAM is a sampled system-wide observation, not model-only allocation. Request duration includes loading; tokens/s covers generation only. First-load conversion can add latency.

The prompt asks for a fenced Python is_even(n) function and project credit. Six integer cases are checked only after a restrictive AST allowlist rejects imports, calls, annotations, docstrings and other code. Formatting rejection can fail the check even when the underlying idea is correct. This small smoke check does not establish broad coding quality or tool-call compatibility.

| Upstream tag | Request seconds | Generation tokens/s | Minimum available RAM GiB | Credit | Python check |
|---|---:|---:|---:|---|---|
| `qwen3.5:0.8b` | 15.15 | 99.08 | 8.76 | Pass | Fail |
| `qwen3.5:4b` | 7.49 | 48.47 | 7.05 | Pass | Fail |
| `qwen3.5:9b` | 50.69 | 29.07 | 4.60 | Pass | Pass |
| `qwen3:0.6b` | 4.75 | 85.22 | 9.67 | Pass | Fail |
| `qwen3:1.7b` | 3.49 | 107.4 | 8.89 | Pass | Fail |
| `qwen3:4b-q4_K_M` | 5.49 | 58.69 | 7.45 | Pass | Fail |
| `qwen3:4b-instruct-2507-q4_K_M` | 5.44 | 61.53 | 7.69 | Pass | Pass |
| `qwen3:4b-thinking-2507-q4_K_M` | 12.93 | 59.52 | 7.72 | Pass | Pass |
| `qwen3:8b` | 7.77 | 34.41 | 5.33 | Pass | Fail |
| `gemma4:e2b` | 17.65 | 35.94 | 8.05 | Pass | Pass |
| `gemma4:e4b` | 13.24 | 51.15 | 5.62 | Pass | Pass |
| `granite4:1b` | 5.91 | 56.54 | 6.21 | Fail | Pass |
| `granite4:3b` | 35.65 | 59.69 | 5.92 | Pass | Pass |
| `ministral-3:3b` | 44.06 | 62.38 | 4.84 | Pass | Pass |
| `ministral-3:8b` | 113.88 | 29.76 | 4.68 | Pass | Pass |

[Raw synthetic outputs and measurements](local50-smoke-snapshot.json). Weight and profile identities were revalidated when this snapshot was built. Subsequent changes require fresh verification.

An earlier qwen3.5:2b download exceeded its transport retry budget. Its partial data was retained; it is not counted in this snapshot. Other candidates remain pending. See [the reviewed candidates](../local50-models.json) and [installation guide](../LOCAL50.md).
