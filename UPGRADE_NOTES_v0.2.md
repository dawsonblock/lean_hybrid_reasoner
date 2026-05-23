# Upgrade Notes v0.2

## Implemented hardening

1. **Strict budget enforcement**
   - Added `max_total_tactics`.
   - Added `max_repair_attempts`.
   - Search exits with `budget_exceeded` when tactic budget is hit.

2. **Progress-aware search scoring**
   - Added penalty for accepted tactics that leave goals unchanged.
   - Added penalty when goals increase.
   - Branch score now prefers real progress, not merely accepted tactics.

3. **Prompt-state control**
   - Added deterministic middle-truncation for proof state rendering.
   - `as_prompt_text()` supports `max_section_chars` and `max_total_chars`.
   - Added compact state keys for duplicate/stagnant branch pruning.

4. **Real Lean transition adapter**
   - Added `LeanCliBackend` using `lake env lean` or `lean`.
   - Supports theorem listing/loading for simple one-line theorem declarations.
   - Executes proof prefix + one candidate tactic inside a temporary Lean file.
   - Classifies solved, unsolved-goals partial state, or tactic failure.

5. **Retrieval upgrade**
   - Replaced raw token overlap with dependency-free BM25-style scoring.
   - Added Lean declaration parser for theorem/lemma premise indexing.

6. **Observability upgrade**
   - Added `trace-summary` CLI.
   - Added HTML dashboard generation.
   - Added DOT proof-tree export.

7. **DSPy seam**
   - Added `DSPyTacticProposer` adapter with lazy optional import.
   - Keeps base repo runnable without DSPy installed.

## Remaining real work

- Replace subprocess text parsing with LeanDojo-v2 exact proof-state APIs.
- Build a Mathlib-scale premise index.
- Add persisted compiled DSPy programs.
- Add LangGraph checkpoint persistence for long proof runs.
- Build a benchmark suite with increasing theorem complexity.
