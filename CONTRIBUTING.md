# Help test Foreman on real hardware

Useful contributions are reproducible hardware reports, small failing coding examples, documentation fixes, and reviewed style conversations. There is no expectation to buy a GPU or pay for an API.

## Report a result

Open a [GitHub issue](https://github.com/kawinthorn11-collab/foreman-30b/issues) titled `Hardware report: GPU / RAM / quantization`. Include:

- GPU, VRAM, RAM, OS, driver and Ollama versions.
- Context length, GPU layers, output limit, and whether other model workloads were running.
- Exact sanitized prompt, complete response, cold/warm timing, and generation tokens/sec.
- Available system RAM and total GPU use if measured. Explain whether metrics include other apps.
- A small reproducible check, including failures. Do not generalize one passing example into a capability claim.

Remove API keys, private file paths, user data, and confidential code before posting. Hardware reports are public. Do not run unreviewed generated code to obtain results.

## Style examples

Edit `data/style-draft.jsonl` and explain changes. All 24 original examples are pending human review. Do not upload private conversations or data without the right to share it. A reviewed style seed is not enough to claim improved coding skill.

## Source changes

Keep changes focused. Run `python -m unittest discover -s tests -v` and `python scripts/project.py validate`. Report exactly what was tested. The current server ownership check is Windows-specific; do not advertise Linux support without implementing and verifying it.

If the project helps you, a star makes it easier to find again. Share real results rather than artificial downloads or engagement.
