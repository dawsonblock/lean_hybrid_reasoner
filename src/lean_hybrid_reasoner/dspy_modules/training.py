from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import metadata
import os
from pathlib import Path
from random import Random
from statistics import mean
from typing import Any, Literal

from lean_hybrid_reasoner.cli_errors import DSPyUnavailableError, InvalidDatasetError
from lean_hybrid_reasoner.dspy_modules.dataset import (
    DspyTacticExample,
    load_repair_examples_file,
    load_repair_examples_pack,
    load_repair_examples,
    load_tactic_examples_file,
    load_tactic_examples_pack,
    load_tactic_examples,
    to_dspy_examples,
)
from lean_hybrid_reasoner.dspy_modules.metrics import tactic_match_or_accept_metric
from lean_hybrid_reasoner.dspy_modules.signatures import RepairTactic, SuggestTactic
from lean_hybrid_reasoner.dspy_modules.manifest import (
    CompiledProgramManifest,
    write_compiled_artifact,
)


@dataclass
class TrainingRunReport:
    target: Literal["proposer", "repairer"]
    dry_run: bool
    loaded_examples: int
    kept_examples: int
    dropped_examples: int
    invalid_tactic_count: int
    train_examples: int
    dev_examples: int
    output_dir: str


def _require_dspy() -> str:
    try:
        import dspy
    except Exception as exc:
        raise DSPyUnavailableError(
            'DSPy is not installed.\nInstall with: pip install -e ".[llm]"'
        ) from exc
    try:
        version = metadata.version("dspy-ai")
    except Exception:
        version = "unknown"
    return version


def _ensure_dspy_lm_configured() -> str:
    import dspy

    current_lm = getattr(dspy.settings, "lm", None)
    if current_lm is not None:
        return str(current_lm)

    model_name = os.getenv("LHR_DSPY_MODEL")
    if not model_name:
        raise DSPyUnavailableError(
            "DSPy model is not configured. Set LHR_DSPY_MODEL or configure dspy.settings.lm before training."
        )

    try:
        dspy.configure(lm=dspy.LM(model_name))
        return model_name
    except Exception as exc:
        raise DSPyUnavailableError(
            f"Failed to configure DSPy model '{model_name}'. Check provider credentials and model string."
        ) from exc


def _load_examples(
    target: Literal["proposer", "repairer"], dataset_path: Path
) -> list[DspyTacticExample]:
    if not dataset_path.exists():
        raise InvalidDatasetError(f"Dataset path not found: {dataset_path}")
    if target == "proposer":
        return load_tactic_examples(dataset_path)
    return load_repair_examples(dataset_path)


def _load_split_examples(
    *,
    target: Literal["proposer", "repairer"],
    dataset: Path,
    devset: Path | None,
) -> tuple[list[DspyTacticExample], list[DspyTacticExample]]:
    if not dataset.exists():
        raise InvalidDatasetError(f"Dataset path not found: {dataset}")
    if devset is not None and not devset.exists():
        raise InvalidDatasetError(f"Dataset path not found: {devset}")

    if target == "proposer":
        load_file = load_tactic_examples_file
        load_pack = load_tactic_examples_pack
    else:
        load_file = load_repair_examples_file
        load_pack = load_repair_examples_pack

    if devset is not None:
        if dataset.is_dir():
            train_examples, _ = load_pack(dataset)
        else:
            train_examples = load_file(dataset)

        if devset.is_dir():
            _, dev_examples = load_pack(devset)
        else:
            dev_examples = load_file(devset)
        return train_examples, dev_examples

    if dataset.is_dir():
        return load_pack(dataset)
    return load_file(dataset), []


def _apply_limits(
    examples: list[DspyTacticExample],
    *,
    max_examples: int | None,
    seed: int,
) -> list[DspyTacticExample]:
    if max_examples is None or max_examples <= 0 or len(examples) <= max_examples:
        return examples
    shuffled = list(examples)
    Random(seed).shuffle(shuffled)
    return shuffled[:max_examples]


def _extract_tactic_from_prediction(prediction: Any) -> dict[str, str]:
    raw = getattr(prediction, "tactic_candidates", None)
    if raw is None:
        raw = getattr(prediction, "repaired_tactic", None)
    if isinstance(raw, list) and raw:
        return {"tactic": str(raw[0])}
    if isinstance(raw, str):
        return {"tactic": raw}
    return {"tactic": str(raw or "")}


def _normalize_metric_name(metric: str) -> tuple[str, str | None]:
    metric_name = metric.strip().lower()
    if metric_name == "verifier":
        return "verifier_proxy", (
            "Metric 'verifier' is deprecated and currently aliases to "
            "'verifier_proxy' (offline-safe validity proxy)."
        )
    return metric_name, None


def _build_metric(metric: str):
    metric_name, _ = _normalize_metric_name(metric)

    if metric_name == "exact":

        def _exact(example: Any, prediction: Any, trace: Any = None) -> float:
            pred = _extract_tactic_from_prediction(prediction)
            target = str(getattr(example, "target_tactic", "") or "").strip()
            tactic = str(pred.get("tactic") or "").strip()
            return 1.0 if target and tactic == target else 0.0

        return _exact

    if metric_name == "verifier_proxy":
        # Full verifier-loop optimization is supported by evaluation metrics; training compile uses
        # a deterministic tactic-validity proxy to keep local/offline behavior stable.
        def _verifier_proxy(example: Any, prediction: Any, trace: Any = None) -> float:
            pred = _extract_tactic_from_prediction(prediction)
            return tactic_match_or_accept_metric(
                {"target_tactic": getattr(example, "target_tactic", "")}, pred
            )

        return _verifier_proxy

    def _sanitized(example: Any, prediction: Any, trace: Any = None) -> float:
        pred = _extract_tactic_from_prediction(prediction)
        return tactic_match_or_accept_metric(
            {"target_tactic": getattr(example, "target_tactic", "")}, pred
        )

    return _sanitized


def _build_program(target: Literal["proposer", "repairer"]):
    import dspy

    if target == "proposer":
        if SuggestTactic is None:
            raise DSPyUnavailableError(
                "SuggestTactic signature unavailable; install DSPy extras."
            )
        return dspy.Predict(SuggestTactic)
    if RepairTactic is None:
        raise DSPyUnavailableError(
            "RepairTactic signature unavailable; install DSPy extras."
        )
    return dspy.Predict(RepairTactic)


def _compile_program(
    *,
    program: Any,
    trainset: list[Any],
    devset: list[Any],
    optimizer: str,
    metric_fn: Any,
) -> Any:
    import dspy

    opt_name = optimizer.strip().lower()
    if opt_name == "none":
        return program

    if opt_name == "bootstrap":
        teleprompter = dspy.BootstrapFewShot(metric=metric_fn)
        return teleprompter.compile(program, trainset=trainset, valset=devset or None)

    if opt_name == "mipro":
        if not hasattr(dspy, "MIPROv2"):
            raise DSPyUnavailableError(
                "MIPRO optimizer not available in this DSPy version."
            )
        teleprompter = dspy.MIPROv2(metric=metric_fn, auto="light")
        return teleprompter.compile(program, trainset=trainset, valset=devset or None)

    raise InvalidDatasetError("optimizer must be one of: bootstrap, mipro, none")


def _predict_for_example(
    *,
    target: Literal["proposer", "repairer"],
    program: Any,
    example: DspyTacticExample,
) -> Any:
    if target == "proposer":
        return program(
            theorem_statement=example.theorem_statement,
            proof_state=example.proof_state,
            retrieved_premises=example.retrieved_premises,
        )
    failed_tactic = example.failed_tactics[0] if example.failed_tactics else ""
    return program(
        theorem_statement=example.theorem_statement,
        proof_state=example.proof_state,
        failed_tactic=failed_tactic,
        lean_error="",
    )


def _evaluate_program(
    *,
    target: Literal["proposer", "repairer"],
    program: Any,
    metric_fn: Any,
    examples: list[DspyTacticExample],
) -> dict[str, float]:
    if not examples:
        return {
            "score": 0.0,
            "dev_score_mean": 0.0,
            "dev_examples": 0.0,
            "invalid_output_rate": 0.0,
            "exact_match_rate": 0.0,
            "sanitized_valid_rate": 0.0,
        }

    metric_scores: list[float] = []
    invalid_outputs = 0
    exact_matches = 0
    sanitized_valid = 0

    for example in examples:
        prediction = _predict_for_example(
            target=target, program=program, example=example
        )
        pred = _extract_tactic_from_prediction(prediction)
        tactic = str(pred.get("tactic") or "")
        sanitized = tactic_match_or_accept_metric(
            {"target_tactic": example.target_tactic},
            {"tactic": tactic},
        )
        score = float(metric_fn(example, prediction, None))
        metric_scores.append(score)

        if sanitized <= 0.0:
            invalid_outputs += 1
        else:
            sanitized_valid += 1
        if (
            tactic.strip() == example.target_tactic.strip()
            and example.target_tactic.strip()
        ):
            exact_matches += 1

    total = float(len(examples))
    mean_score = float(mean(metric_scores))
    return {
        "score": mean_score,
        "dev_score_mean": mean_score,
        "dev_examples": total,
        "invalid_output_rate": invalid_outputs / total,
        "exact_match_rate": exact_matches / total,
        "sanitized_valid_rate": sanitized_valid / total,
    }


def run_training(
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
    train_examples, dev_examples = _load_split_examples(
        target=target,
        dataset=dataset,
        devset=devset,
    )

    loaded = len(train_examples)
    train_examples = _apply_limits(
        train_examples, max_examples=max_train_examples, seed=seed
    )
    dev_examples = _apply_limits(dev_examples, max_examples=max_dev_examples, seed=seed)

    if not train_examples:
        if target == "repairer":
            raise InvalidDatasetError(
                "No valid repair examples found. Run proofs that generate repair_tactic events, use --include-failures, or train only the proposer."
            )
        raise InvalidDatasetError("No valid training examples found after filtering.")

    metric_name, metric_warning = _normalize_metric_name(metric)

    report = TrainingRunReport(
        target=target,
        dry_run=dry_run,
        loaded_examples=loaded,
        kept_examples=len(train_examples),
        dropped_examples=max(0, loaded - len(train_examples)),
        invalid_tactic_count=max(0, loaded - len(train_examples)),
        train_examples=len(train_examples),
        dev_examples=len(dev_examples),
        output_dir=str(output),
    )

    if dry_run:
        payload = {
            "target": report.target,
            "dry_run": True,
            "examples_loaded": report.loaded_examples,
            "examples_kept": report.kept_examples,
            "examples_dropped": report.dropped_examples,
            "invalid_tactic_count": report.invalid_tactic_count,
            "estimated_train_size": report.train_examples,
            "estimated_dev_size": report.dev_examples,
            "required_dspy_fields_missing": [],
        }
        if metric_warning:
            payload["warnings"] = [metric_warning]
        return payload

    dspy_version = _require_dspy()
    model_name = _ensure_dspy_lm_configured()

    trainset = to_dspy_examples(train_examples)
    dspy_devset = to_dspy_examples(dev_examples) if dev_examples else []
    program = _build_program(target)
    metric_fn = _build_metric(metric_name)
    compiled_program = _compile_program(
        program=program,
        trainset=trainset,
        devset=dspy_devset,
        optimizer=optimizer,
        metric_fn=metric_fn,
    )

    dspy_program_dir = output / "dspy_program"
    dspy_program_dir.mkdir(parents=True, exist_ok=True)
    if hasattr(compiled_program, "save"):
        compiled_program.save(str(dspy_program_dir))
    else:
        raise DSPyUnavailableError("Compiled DSPy program could not be saved.")

    package_version = "0.0.0"
    try:
        package_version = metadata.version("lean-hybrid-reasoner")
    except Exception:
        pass

    score_examples = dev_examples if dev_examples else train_examples
    score_source = "dev" if dev_examples else "train_proxy"
    score_payload = _evaluate_program(
        target=target,
        program=compiled_program,
        metric_fn=metric_fn,
        examples=score_examples,
    )
    manifest = CompiledProgramManifest(
        artifact_type=target,
        created_at=datetime.now(timezone.utc).isoformat(),
        package_version=package_version,
        dspy_version=dspy_version,
        model=model_name,
        optimizer=optimizer,
        train_dataset=str(dataset),
        dev_dataset=str(devset) if devset else None,
        train_examples=len(train_examples),
        dev_examples=len(dev_examples),
        metric_name=metric_name,
        scores=score_payload,
        config_snapshot={"seed": seed, "score_source": score_source},
    )

    write_compiled_artifact(
        output_dir=output,
        manifest=manifest,
        metrics={**score_payload, "metric": metric_name, "score_source": score_source},
        program_payload={
            "artifact_type": target,
            "optimizer": optimizer,
            "metric": metric_name,
            "train_examples": len(train_examples),
            "dev_examples": len(dev_examples),
            "dspy_program_dir": "dspy_program",
        },
    )

    payload = {
        "target": target,
        "dry_run": False,
        "output": str(output),
        "train_examples": len(train_examples),
        "dev_examples": len(dev_examples),
        "metric": metric_name,
        "score": score_payload["score"],
    }
    if metric_warning:
        payload["warnings"] = [metric_warning]
    return payload
