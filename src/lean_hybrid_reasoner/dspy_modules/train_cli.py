from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from lean_hybrid_reasoner.dspy_modules.training import run_training


def train_dspy_target(
    *,
    target: Literal["proposer", "repairer"],
    dataset: Path,
    devset: Path | None,
    output: Path,
    optimizer: str,
    metric: str,
    max_train_examples: int,
    max_dev_examples: int,
    seed: int,
    dry_run: bool,
) -> dict[str, Any]:
    return run_training(
        target=target,
        dataset=dataset,
        devset=devset,
        output=output,
        optimizer=optimizer,
        metric=metric,
        max_train_examples=max_train_examples,
        max_dev_examples=max_dev_examples,
        seed=seed,
        dry_run=dry_run,
    )
