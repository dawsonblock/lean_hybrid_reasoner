# Upgrade Notes v0.3

## Implemented upgrades

1. **DSPy repair seam**
   - Added `DSPyTacticRepairer`.
   - Added robust DSPy output normalization for list/string/JSON/dict outputs.
   - Added lazy loading for compiled DSPy proposer and repairer programs.

2. **Semantic retrieval seam**
   - Added dependency-free `HashingSemanticPremiseIndex`.
   - Added optional `SentenceTransformerPremiseIndex` using sentence-transformers + FAISS.
   - Added retrieval mode selection via `LHR_RETRIEVAL_MODE`.

3. **Budget tuning**
   - Added named budget profiles.
   - Added `budget-sweep` CLI command.
   - Added `max_stagnant_steps` budget.

4. **Trace analytics**
   - Added tactic histograms.
   - Added error histograms.
   - Added branch prune/dead-reason analysis.
   - Added per-run budget pressure analysis.
   - Dashboard now embeds analytics per run.

5. **Search hardening**
   - Duplicate-state pruning now keys only on theorem/goals/hypotheses, not proof suffix.
   - Accepted no-progress branches accumulate `stagnant_steps`.
   - Stagnation can now terminate a branch before it burns the wider tactic budget.

6. **Metrics expansion**
   - Added `budget_failure_rate`.
   - Added `median_steps_to_qed`.
   - Main score penalizes timeout/budget failure.

## Remaining real work

- Implement a real LeanDojo-v2 client with exact proof-state extraction.
- Add persisted premise indexes for large Lean projects.
- Add compiled DSPy training/evaluation scripts.
- Add a theorem-difficulty curriculum beyond starter examples.
- Add cache-aware Lean CLI mode to reduce file recompilation overhead.
- Add LangGraph checkpoint persistence for long proof runs.
