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
