---
name: puzzle-solving
description: Legacy compatibility alias. Use only when the user explicitly invokes `$puzzle-solving` or asks for the legacy puzzle-solving skill by name; delegate immediately to `$run-puzzle-collaboration` and do not apply a separate solving workflow.
---

# Puzzle Solving Compatibility Alias

Treat this skill as a deprecated name, not an independent puzzle-solving system.

1. Invoke `$run-puzzle-collaboration` immediately and follow it as the sole authoritative workflow.
2. Let `$run-puzzle-collaboration` invoke `$visual-puzzle-transcriber` when visual evidence requires transcription.
3. Do not recreate, merge, or selectively reuse the former `puzzle-solving` workflow.
4. If `$run-puzzle-collaboration` is unavailable, tell the user that the replacement skill must be installed; do not silently fall back to legacy behavior.

