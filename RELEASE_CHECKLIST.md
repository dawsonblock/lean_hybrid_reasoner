# Release Checklist

Use this checklist before publishing a release archive.

## Validation

- [ ] `pytest` passes.
- [ ] `hybrid-proof validate-traces --input .runs/traces.jsonl --strict` passes for canonical traces.
- [ ] Legacy trace migration path verified:
  - [ ] `hybrid-proof migrate-traces --input <legacy>.jsonl --output <migrated>.jsonl`
  - [ ] `hybrid-proof validate-traces --input <migrated>.jsonl --strict`

## Core smoke checks

- [ ] `hybrid-proof doctor` passes in expected environment.
- [ ] `hybrid-proof list-theorems` works for selected backend.
- [ ] `hybrid-proof run --theorem and_comm_example` succeeds on mock backend.
- [ ] `hybrid-proof replay --index -1 --verify-with-lean --json` verified for selected backend.
- [ ] `hybrid-proof failure-report --group-by theorem` output looks correct.

## Dataset and traces

- [ ] `hybrid-proof pack-dataset --min-quality accepted` generates train/dev JSONL.
- [ ] Dataset manifest contains `schema_version: 0.6` and `quality_filter` summary.
- [ ] Trace schema version fields present in run records.

## Docs and notes

- [ ] README command examples updated.
- [ ] `UPGRADE_NOTES_v0.8.md` updated with final changes.
- [ ] Release checklist reviewed and completed.
