# DSPy Training Guide

## Install optional DSPy dependencies

```bash
pip install -e ".[llm]"
```

## Build dataset pack

```bash
hybrid-proof pack-dataset \
  --output-dir .runs/dataset_pack \
  --target proposer \
  --min-quality accepted \
  --exclude-invalid-tactics
```

## Dry-run proposer training

```bash
hybrid-proof train-dspy-proposer \
  --dataset .runs/dataset_pack/train.jsonl \
  --devset .runs/dataset_pack/dev.jsonl \
  --output .compiled/proposer \
  --dry-run
```

Notes:

- When `--dataset` and `--devset` are explicit JSONL files, they are loaded independently.
- Passing a dataset-pack directory to `--dataset` loads `train.jsonl` for training and `dev.jsonl` for dev by default.
- `--metric verifier_proxy` is an offline-safe tactic-validity proxy.
- `--metric verifier` remains a deprecated alias to `verifier_proxy`.

## Execute proposer training

```bash
hybrid-proof train-dspy-proposer \
  --dataset .runs/dataset_pack/train.jsonl \
  --devset .runs/dataset_pack/dev.jsonl \
  --output .compiled/proposer
```

## Repairer training

```bash
hybrid-proof train-dspy-repairer \
  --dataset .runs/dataset_pack/train.jsonl \
  --devset .runs/dataset_pack/dev.jsonl \
  --output .compiled/repairer
```

## Compare heuristic vs DSPy proposer

```bash
hybrid-proof compare-proposers --left heuristic --right dspy --json
```

## Runtime fallback when DSPy is unavailable

Set fallback to heuristic for runtime proposer/repairer selection:

```bash
export LHR_DSPY_FALLBACK=heuristic
```

Training commands do not fallback and will fail with an install hint if DSPy is missing.
