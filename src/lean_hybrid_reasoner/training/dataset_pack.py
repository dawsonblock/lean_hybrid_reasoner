from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lean_hybrid_reasoner.training.quality_filters import apply_quality_filter
from lean_hybrid_reasoner.training.trace_dataset import (
    extract_training_examples,
    summarize_training_examples,
)
from lean_hybrid_reasoner.traces.dashboard import load_trace_records


def deterministic_split(
    examples: list[dict[str, Any]], dev_ratio: float = 0.2
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not examples:
        return [], []
    dev_every = max(2, round(1 / dev_ratio)) if dev_ratio > 0 else len(examples) + 1
    train: list[dict[str, Any]] = []
    dev: list[dict[str, Any]] = []
    for idx, example in enumerate(examples):
        item = {**example, "example_id": f"ex_{idx:06d}"}
        if idx % dev_every == 0:
            dev.append(item)
        else:
            train.append(item)
    if not train and dev:
        train.append(dev.pop())
    return train, dev


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_dataset_pack(
    trace_path: str | Path,
    output_dir: str | Path,
    *,
    include_failures: bool = False,
    include_repairs: bool = True,
    min_quality: str = "any",
    dev_ratio: float = 0.2,
) -> dict[str, Any]:
    records = load_trace_records(trace_path)
    examples = extract_training_examples(
        records, include_failures=include_failures, include_repairs=include_repairs
    )
    filtered_examples, filter_summary = apply_quality_filter(
        examples, min_quality=min_quality
    )
    train, dev = deterministic_split(filtered_examples, dev_ratio=dev_ratio)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _write_jsonl(output / "train.jsonl", train)
    _write_jsonl(output / "dev.jsonl", dev)
    summary = summarize_training_examples(filtered_examples)
    manifest = {
        "schema_version": "0.6",
        "source_trace_path": str(trace_path),
        "include_failures": include_failures,
        "include_repairs": include_repairs,
        "min_quality": min_quality,
        "dev_ratio": dev_ratio,
        "total_examples": len(filtered_examples),
        "examples_before_filter": len(examples),
        "train_examples": len(train),
        "dev_examples": len(dev),
        "quality_filter": filter_summary,
        "summary": summary,
        "files": {
            "train": "train.jsonl",
            "dev": "dev.jsonl",
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return manifest
