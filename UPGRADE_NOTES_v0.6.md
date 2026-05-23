# Upgrade Notes v0.6

This release begins the v0.6 hardening track with schema-versioned traces and migration tooling.

## Added

- v0.6 trace schema contract with run-level fields:
  - `trace_schema_version`
  - `run_id`
- Canonical v0.6 trace event normalization while preserving legacy `event` compatibility keys.
- `hybrid-proof validate-traces` command for validating trace JSONL files.
- `hybrid-proof migrate-traces` command for upgrading legacy trace files to v0.6 format.
- Namespace-aware Lean declaration parser for `theorem`, `lemma`, `example`, and `def`.
- Lean sandbox execution module with temp retention controls (`LHR_KEEP_LEAN_TEMP`, `LHR_LEAN_TEMP_DIR`).
- Structured Lean error categorization with optional line/column and suggestion metadata.
- `hybrid-proof replay --verify-with-lean` verification mode (when backend supports verifier hook).
- Tactic memory suppression to avoid repeating known-failed tactics for the same state.
- Dataset quality filtering via `pack-dataset --min-quality {any|accepted|solved}`.
- Failure report theorem grouping via `hybrid-proof failure-report --group-by theorem`.
- Release gate helper script: `scripts/release_v06_check.sh`.
- Compatibility aliases:
  - `hybrid-proof trace-validate`
  - `hybrid-proof trace-migrate`

## Changed

- Package version updated to `0.6.0`.
- Config snapshot schema version updated to `0.6`.
- Search engine trace output now emits canonicalized v0.6 event shape.
- `pack-dataset` manifest now uses schema version `0.6` and includes quality filter summaries.

## Commands

```bash
hybrid-proof validate-traces --input .runs/traces.jsonl
hybrid-proof validate-traces --input .runs/traces.jsonl --strict --json

hybrid-proof migrate-traces --input .runs/old_traces.jsonl --output .runs/traces_v06.jsonl
hybrid-proof migrate-traces --input .runs/old_traces.jsonl --output .runs/traces_v06.jsonl --json

hybrid-proof replay --index -1 --verify-with-lean --json
hybrid-proof pack-dataset --include-failures --min-quality accepted --output-dir .runs/dataset_pack_accepted
hybrid-proof failure-report --group-by theorem
bash scripts/release_v06_check.sh
```

## Validation and migration behavior

- Non-strict validation accepts legacy v0.1-v0.5 record shapes and reports them as `legacy_records`.
- Strict validation enforces canonical v0.6 event fields.
- Migration output is deterministic and writes canonical v0.6 events.
- Migration preserves original event payload data under `raw_event`.

## Compatibility notes

- Existing analytics and failure-classification flows remain compatible because canonical events preserve legacy `event` keys.
- Existing trace consumers can continue to parse trace files without immediate changes.
