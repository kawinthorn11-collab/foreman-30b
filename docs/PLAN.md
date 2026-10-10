# Foreman 30B implementation plan

Goal: deliver a measured local 30B coding prototype and a reproducible, honest GitHub-ready customization project.
Architecture: standard-library Python tooling drives isolated Ollama; reviewed dataset preparation is separate from future GPU training and GGUF conversion.
Spec: DESIGN.md.

- [x] Download the pinned coding GGUF and verify its checksum.
- [x] Implement bounded local import/run/test tools and test configuration, dataset validation and secret exclusions.
- [x] Create Foreman prompt and synthetic English style conversations for review.
- [x] Add an unexecuted external training/merge/quantization template with reviewed-data and hardware preflight.
- [x] Test real inference identity and two small coding tasks, record token speed and RAM/VRAM. Severe RAM pressure observed; no comfortable-fit claim.
- [ ] Prepare Git repo, model card, attribution and publication instructions; obtain the GitHub destination.

Review focus: insufficient available RAM/VRAM; hash mismatch/interrupted downloads; unreviewed or malformed training examples; accidental secrets/large weights in Git; confusing prompted customization with actual training.
