# Upgrade Notes v0.8.1

This release focuses on DSPy training correctness and runtime fallback clarity.

## Fixed

- Fixed train/dev data leakage when `--dataset` and `--devset` are passed as explicit JSONL files.
- Training now evaluates compiled programs and writes real aggregate score fields instead of placeholder constants.
- Added actionable repairer-specific message when no repair examples are present.
- Added runtime-only DSPy fallback support via `LHR_DSPY_FALLBACK=heuristic` for proposer/repairer selection.
- Added strict/permissive tactic validation modes, keeping strict as default for backward-compatible behavior.
- Added regression tests for split isolation, fallback behavior, doctor formatting, and version metadata alignment.

## Metric Semantics

- `verifier_proxy` is now the canonical offline-safe verifier-like metric name.
- `verifier` is kept as a deprecated alias for compatibility.

## Notes

- Training commands still fail loudly when DSPy is missing, with an install hint.
- Fallback behavior applies to runtime proposer/repairer selection only.
