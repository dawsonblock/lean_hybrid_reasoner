# Upgrade Notes v0.5

This release turns the proof-search platform into a more reproducible experiment and training-data workflow.

## Added

- Failure classification for solved runs, timeouts, tactic budget exhaustion, branch budget exhaustion, depth exhaustion, stagnation, duplicate-state loops, tactic errors, and frontier exhaustion.
- `hybrid-proof failure-report` for triaging trace files.
- `hybrid-proof compare-traces` for comparing two trace files or experiment variants.
- `hybrid-proof pack-dataset` for producing a train/dev JSONL dataset pack plus manifest from proof traces.
- `hybrid-proof snapshot-config` for saving current LHR_* settings, Python/platform metadata, and Lean/Lake availability.
- Trace analytics now include failure categories and recommended actions.

## Why this matters

The earlier builds could run and visualize proof search. v0.5 adds the missing experiment-governance layer: you can now capture the configuration that produced a run, classify why failures happened, compare two variants, and package traces into training data without manually scraping JSON.

## New Commands

```bash
hybrid-proof failure-report
hybrid-proof compare-traces --left .runs/baseline.jsonl --right .runs/variant.jsonl
hybrid-proof pack-dataset --output-dir .runs/dataset_pack
hybrid-proof snapshot-config --output .runs/config_snapshot.json
```

## Notes

Failure classification is heuristic and trace-derived. Lean/kernel verification remains the authority for proof correctness.
