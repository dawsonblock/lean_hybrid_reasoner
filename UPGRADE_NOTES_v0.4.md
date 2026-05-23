# Upgrade Notes v0.4

v0.4 adds the practical experimentation layer needed before serious DSPy or LeanDojo integration.

## Added

- `hybrid-proof doctor`
  - Checks backend support, trace path writability, Lean/Lake availability, local Lean file paths, and optional DSPy/LangGraph/semantic dependencies.

- `hybrid-proof trace-export-dspy`
  - Converts trace records into JSONL training examples for tactic suggestion and tactic repair.
  - Supports accepted-only examples by default and optional failure examples via `--include-failures`.

- `hybrid-proof replay`
  - Replays a recorded proof against the selected backend.
  - Useful for regression checks when Lean files, Lean versions, or backend adapters change.

- `hybrid-proof experiment-grid`
  - Runs starter evaluations across budget profile and retrieval mode combinations.
  - Intended for quick comparison of search and retrieval settings.

- `LHR_LEAN_TIMEOUT`
  - Configures Lean CLI subprocess timeout.

## Changed

- Package version moved to `0.4.0`.
- Lean CLI backend now records timeout metadata in execution results.
- Test count increased to 25.

## Not changed

- Mock backend remains default.
- Lean CLI backend remains a lightweight transition adapter, not a replacement for LeanDojo-v2.
- DSPy modules remain adapter seams; no model is bundled.

## Next recommended upgrade

The next meaningful upgrade is a real LeanDojo-v2 backend that emits exact proof-state snapshots into trace events. That will make `trace-export-dspy` much more valuable because training examples will contain formal states, not reconstructed approximations from branch expansion logs.
