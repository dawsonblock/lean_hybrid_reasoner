# Lean Hybrid Reasoner v0.6

Runnable experimentation platform for a controllable hybrid neuro-symbolic theorem prover.

The design keeps the LLM out of the authority path. Neural or heuristic modules propose tactics and repairs. A Lean-style backend executes and verifies. The search engine manages bounded branches, traceability, duplicate-state pruning, stagnation control, retrieval, replay, diagnostics, training-data export, failure classification, dataset packaging, configuration snapshots, and budget reporting.

## What changed in v0.6

This upgraded zip starts the trace-hardening track on top of v0.5:

- Versioned trace run records now emit `trace_schema_version: "0.6"` and per-run `run_id`.
- Search traces are canonicalized with v0.6 event fields while preserving backward-compatible legacy event keys.
- `validate-traces` command validates trace JSONL files and reports structured diagnostics.
- `migrate-traces` command upgrades legacy trace JSONL files into canonical v0.6 format.
- Compatibility aliases are included: `trace-validate` and `trace-migrate`.
- Trace validation supports non-strict legacy acceptance and strict v0.6 enforcement.

v0.5 capabilities remain included:

This release retains the experiment-governance layer added in v0.5:

- Failure classification for solved runs, timeouts, budget exhaustion, depth exhaustion, stagnation, duplicate-state loops, tactic errors, and frontier exhaustion.
- `failure-report` command for triaging trace files into stable failure categories with suggested next actions.
- `compare-traces` command for comparing baseline vs. variant runs.
- `pack-dataset` command for producing train/dev JSONL splits plus a manifest.
- `snapshot-config` command for capturing `LHR_*` settings, Python/platform metadata, and Lean/Lake availability.
- Trace analytics now include failure categories and recommended actions.

v0.4 capabilities remain included:

- Trace-to-training-data export for DSPy/fine-tuning bootstrap datasets.
- `doctor` diagnostics command for backend, Lean/Lake, trace path, DSPy, LangGraph, and semantic retrieval readiness.
- Proof replay command to revalidate recorded proofs against the selected backend.
- Experiment grid command for budget-profile × retrieval-mode comparison.
- Lean CLI timeout is configurable with `LHR_LEAN_TIMEOUT`.
- Lean CLI execution metadata now records timeout/category information.
- Tests expanded to cover dataset export, diagnostics, proof replay, and experiment grid.

v0.3 capabilities remain included:

- DSPy proposer and repairer seams.
- DSPy output normalization.
- BM25 retrieval default.
- Dependency-free semantic retrieval mode.
- Optional sentence-transformers + FAISS retrieval adapter.
- Budget profiles: `tiny`, `starter`, `wide`, `deep`, `aggressive`.
- Trace analytics, dashboard, and DOT proof-tree export.
- Stagnation budget and duplicate-state pruning.

The mock backend remains the default because it gives deterministic validation of the control loop before installing Lean or connecting an LLM.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Optional LLM graph dependencies:

```bash
pip install -e ".[dev,llm]"
```

Optional semantic retrieval dependencies:

```bash
pip install -e ".[dev,semantic]"
```

## Run tests

```bash
pytest
```

Expected in this zip:

```text
49 tests passed
```

## Run diagnostics

```bash
hybrid-proof doctor
hybrid-proof doctor --json
```

This checks whether the selected backend is usable, whether trace output is writable, whether Lean/Lake are on `PATH`, and whether optional DSPy/LangGraph/semantic packages are installed.

## Run with the mock backend

```bash
hybrid-proof list-theorems
hybrid-proof run --theorem add_zero_example
hybrid-proof run --theorem and_comm_example --print-trace
hybrid-proof eval
```

Expected successful examples:

- `add_zero_example`
- `zero_add_example`
- `and_comm_example`

Expected failing example:

- `impossible_example`

## Budget profiles and sweep

```bash
hybrid-proof run --theorem and_comm_example --budget-profile tiny
hybrid-proof run --theorem and_comm_example --budget-profile starter
hybrid-proof budget-sweep
hybrid-proof budget-sweep --json
```

Profiles are defined in `search/budgets.py`:

```text
tiny       shallow smoke-test budget
starter    default development budget
wide       more branch exploration
deep       deeper proof chains
aggressive large local search budget
```

For hard theorems, increase `max_total_tactics` and `max_branches` before increasing depth. Branching factor usually dominates.

## Experiment grid

Compare retrieval modes and budget profiles together:

```bash
hybrid-proof experiment-grid
hybrid-proof experiment-grid --budget-profiles tiny,starter,wide --retrieval-modes bm25,semantic --json
```

This is the first useful workflow for data-driven tuning. Change one variable at a time, then inspect completion rate, tactic accept rate, and score.

## Retrieval modes

Default BM25-style retrieval:

```bash
export LHR_RETRIEVAL_MODE=bm25
```

Dependency-free semantic fallback:

```bash
export LHR_RETRIEVAL_MODE=semantic
```

Optional sentence-transformers + FAISS retrieval:

```bash
pip install -e ".[semantic]"
export LHR_RETRIEVAL_MODE=sentence_transformers
export LHR_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

The hashing semantic mode is not a real Lean-aware embedding model. It is a local seam that keeps the retrieval interface testable before heavier embedding dependencies are installed.

## DSPy proposer and repairer seams

Heuristic mode is default:

```bash
export LHR_PROPOSER=heuristic
export LHR_REPAIRER=heuristic
```

DSPy mode:

```bash
pip install -e ".[llm]"
export LHR_PROPOSER=dspy
export LHR_REPAIRER=dspy
export LHR_DSPY_PROPOSER_PATH=.compiled/proposer.json
export LHR_DSPY_REPAIRER_PATH=.compiled/repairer.json
```

The engine only requires these contracts:

```python
proposer.propose(state, max_candidates) -> list[TacticCandidate]
repairer.repair(state, failed_tactic, error_message) -> list[TacticCandidate]
```

This keeps DSPy optimization outside the correctness path. Lean remains the verifier.

## Export traces for DSPy/fine-tuning

After running proofs:

```bash
hybrid-proof trace-export-dspy --output .runs/dspy_examples.jsonl
hybrid-proof trace-export-dspy --include-failures --output .runs/dspy_examples_with_failures.jsonl
```

The exporter creates JSONL examples for:

- `suggest_tactic`
- `repair_tactic`

Each example includes theorem name, branch id, goal snapshot, retrieved premises, tactic, accepted/solved flags, and error metadata when available. This is bootstrap data, not a perfect LeanDojo dataset. Exact proof-state snapshots should later come from the real LeanDojo-v2 backend.

## Package datasets for DSPy/fine-tuning

After running proofs:

```bash
hybrid-proof pack-dataset --output-dir .runs/dataset_pack
hybrid-proof pack-dataset --include-failures --output-dir .runs/dataset_pack_with_failures
hybrid-proof pack-dataset --include-failures --min-quality accepted --output-dir .runs/dataset_pack_accepted
```

This writes:

```text
manifest.json
train.jsonl
dev.jsonl
```

The split is deterministic so experiment runs are repeatable.
`--min-quality accepted` keeps only accepted tactic examples in train/dev output.

## Failure triage and trace comparison

```bash
hybrid-proof failure-report
hybrid-proof failure-report --json
hybrid-proof failure-report --group-by theorem
hybrid-proof compare-traces --left .runs/baseline.jsonl --right .runs/variant.jsonl
```

Failure categories are heuristic and trace-derived. They are for engineering triage, not proof correctness. Lean/kernel acceptance remains the authority.

## Release check automation

```bash
bash scripts/release_v06_check.sh
```

This runs tests and core mock-backend smoke checks used in the v0.6 release gate.

## Snapshot the current configuration

```bash
hybrid-proof snapshot-config --output .runs/config_snapshot.json
hybrid-proof snapshot-config --json
```

Use this before experiment-grid or Lean CLI runs so later results can be traced back to exact `LHR_*` settings and local tool availability.

## Generate trace analytics and dashboard

After running proofs:

```bash
hybrid-proof trace-summary
hybrid-proof trace-analytics
hybrid-proof dashboard --output .runs/dashboard.html
hybrid-proof trace-dot --index -1 > .runs/latest.dot
```

`dashboard.html` is a standalone local HTML report. The DOT output can be rendered with Graphviz if installed.

## Validate and migrate traces

```bash
hybrid-proof validate-traces --input .runs/traces.jsonl
hybrid-proof validate-traces --input .runs/traces.jsonl --strict --json

hybrid-proof migrate-traces --input .runs/old_traces.jsonl --output .runs/traces_v06.jsonl
hybrid-proof migrate-traces --input .runs/old_traces.jsonl --output .runs/traces_v06.jsonl --json
```

Notes:

- Non-strict validation accepts legacy v0.1-v0.5 traces and reports `legacy_records`.
- Strict validation requires canonical v0.6 event fields.
- Migration is deterministic and preserves original event payload data under `raw_event`.

## Replay a recorded proof

```bash
hybrid-proof replay --index -1
hybrid-proof replay --index -1 --json
hybrid-proof replay --index -1 --verify-with-lean --json
```

Replay re-runs the recorded proof against the currently selected backend. This helps detect whether a proof trace still works after changing the Lean file, backend, tactic rules, or Lean version.
When `--verify-with-lean` is enabled and the backend supports proof verification, replay adds a verification report with return code and Lean output snippets.

## Try local Lean subprocess mode

```bash
export LHR_BACKEND=lean_cli
export LHR_LEAN_PROJECT_ROOT=lean_projects/starter
export LHR_LEAN_FILE=HybridStarter.lean
export LHR_LEAN_TIMEOUT=20
hybrid-proof doctor
hybrid-proof list-theorems
hybrid-proof run --theorem add_zero_example
```

This requires Lean/Lake installed on the host. It is a transition adapter, not a full LeanDojo replacement. It compiles a temporary Lean file with the proof prefix and candidate tactic, then classifies the result from Lean output.

For serious proof-state extraction, replace this with LeanDojo-v2 or LeanCopilot behind the same `LeanBackend` protocol.

## Module map

```text
src/lean_hybrid_reasoner/
  cli.py
  settings.py
  schemas/
    proof_state.py
    tactic.py
    branch.py
    result.py
  lean_backend/
    base.py
    mock_backend.py
    lean_cli_backend.py
    dojo_client.py
    error_parser.py
  retrieval/
    premise_index.py
    semantic_index.py
    premise_retriever.py
  dspy_modules/
    heuristic_tactics.py
    dspy_tactics.py
    signatures.py
  search/
    budgets.py
    scoring.py
    frontier.py
    engine.py
  graph/
    state.py
    nodes.py
    build_graph.py
  evals/
    theorem_sets.py
    metrics.py
    run_eval.py
    budget_sweep.py
  experiments/
    experiment_grid.py
    replay.py
    compare.py
  diagnostics/
    doctor.py
    failure_classifier.py
  config/
    snapshot.py
  training/
    trace_dataset.py
    dataset_pack.py
  traces/
    trace_store.py
    analytics.py
    dashboard.py
```

## Correct integration path

1. Snapshot configuration, then validate branch search, budgets, traces, replay, diagnostics, and metrics with the mock backend.
2. Validate `lean_cli` on tiny local Lean files.
3. Export trace datasets and use them for first DSPy proposer/repairer optimization.
4. Replace `LeanCliBackend` with a high-fidelity LeanDojo-v2 backend.
5. Build a larger premise index from Lean declarations.
6. Replace heuristic proposer/repairer with DSPy programs.
7. Optimize against proof completion rate, tactic accept rate, branch efficiency, repair success rate, premise hit rate, and budget failure rate.
8. Only then move toward Mathlib-scale search.

## Correctness boundary

This is not a finished theorem prover. It is a control skeleton that makes proof search explicit, bounded, observable, replayable, and replaceable.

The verifier backend owns correctness. The proposer and repairer only suggest tactics.
