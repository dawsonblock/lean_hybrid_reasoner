from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
import typer

from lean_hybrid_reasoner.lean_backend.mock_backend import MockLeanBackend
from lean_hybrid_reasoner.lean_backend.lean_cli_backend import LeanCliBackend
from lean_hybrid_reasoner.lean_backend.leandojo_v2_client import LeanDojoV2Client
from lean_hybrid_reasoner.search.engine import ProofSearchEngine
from lean_hybrid_reasoner.search.budgets import SearchBudget, named_budget
from lean_hybrid_reasoner.settings import load_settings
from lean_hybrid_reasoner.traces.trace_store import TraceStore
from lean_hybrid_reasoner.traces.dashboard import (
    summarize_trace_file,
    render_html_dashboard,
    load_trace_records,
    proof_tree_dot,
)
from lean_hybrid_reasoner.traces.analytics import analyze_records
from lean_hybrid_reasoner.training.trace_dataset import (
    extract_training_examples,
    write_training_jsonl,
    summarize_training_examples,
)
from lean_hybrid_reasoner.diagnostics.doctor import run_doctor
from lean_hybrid_reasoner.experiments.replay import replay_proof
from lean_hybrid_reasoner.experiments.experiment_grid import run_experiment_grid
from lean_hybrid_reasoner.experiments.compare import compare_trace_sets
from lean_hybrid_reasoner.diagnostics.failure_classifier import classify_records
from lean_hybrid_reasoner.training.dataset_pack import build_dataset_pack
from lean_hybrid_reasoner.config.snapshot import write_config_snapshot
from lean_hybrid_reasoner.traces.validate import validate_trace_file
from lean_hybrid_reasoner.traces.migrate import migrate_trace_file
from lean_hybrid_reasoner.evals.run_eval import run_starter_eval
from lean_hybrid_reasoner.evals.budget_sweep import run_budget_sweep
from lean_hybrid_reasoner.retrieval.premise_retriever import PremiseRetriever
from lean_hybrid_reasoner.dspy_modules.heuristic_tactics import (
    HeuristicTacticProposer,
    HeuristicTacticRepairer,
)

app = typer.Typer(help="Lean Hybrid Reasoner CLI")


def make_backend():
    settings = load_settings()
    if settings.backend == "mock":
        return MockLeanBackend()
    if settings.backend == "lean_cli":
        return LeanCliBackend(
            settings.lean_project_root,
            settings.lean_file,
            timeout_seconds=settings.lean_timeout_seconds,
        )
    if settings.backend in {"leandojo", "leandojo_v2"}:
        return LeanDojoV2Client(
            repo=settings.leandojo_repo,
            commit=settings.leandojo_commit,
            theorem_filter=settings.leandojo_theorem_filter,
            import_module=settings.leandojo_import_module,
        )
    raise typer.BadParameter(
        "Unknown backend. Valid options: mock, lean_cli, leandojo, leandojo_v2."
    )


def make_retriever() -> PremiseRetriever:
    settings = load_settings()
    lean_file = None
    if settings.retrieval_mode != "bm25" and settings.backend == "lean_cli":
        lean_file = str(settings.lean_project_root / settings.lean_file)
    elif settings.retrieval_mode == "bm25" and settings.backend == "lean_cli":
        lean_file = str(settings.lean_project_root / settings.lean_file)
    return PremiseRetriever.from_mode(
        settings.retrieval_mode,
        top_k=settings.retrieval_top_k,
        lean_file=lean_file,
        embedding_model=settings.embedding_model,
    )


def make_proposer():
    settings = load_settings()
    if settings.proposer == "heuristic":
        return HeuristicTacticProposer()
    if settings.proposer == "dspy":
        from lean_hybrid_reasoner.dspy_modules.dspy_tactics import DSPyTacticProposer

        if settings.dspy_proposer_path is None:
            return DSPyTacticProposer(program=None)
        return DSPyTacticProposer.from_compiled(settings.dspy_proposer_path)
    raise typer.BadParameter("Supported proposers: 'heuristic', 'dspy'.")


def make_repairer():
    settings = load_settings()
    if settings.repairer == "heuristic":
        return HeuristicTacticRepairer()
    if settings.repairer == "dspy":
        from lean_hybrid_reasoner.dspy_modules.dspy_tactics import DSPyTacticRepairer

        if settings.dspy_repairer_path is None:
            return DSPyTacticRepairer(program=None)
        return DSPyTacticRepairer.from_compiled(settings.dspy_repairer_path)
    raise typer.BadParameter("Supported repairers: 'heuristic', 'dspy'.")


def make_engine() -> ProofSearchEngine:
    settings = load_settings()
    return ProofSearchEngine(
        backend=make_backend(),
        proposer=make_proposer(),
        repairer=make_repairer(),
        retriever=make_retriever(),
        trace_store=TraceStore(settings.trace_path),
    )


def make_budget(
    max_depth, max_branches, max_seconds, profile: Optional[str]
) -> SearchBudget:
    settings = load_settings()
    if profile:
        base = named_budget(profile)
        data = base.model_dump(exclude={"started_at"})
    else:
        data = {
            "max_depth": settings.max_depth,
            "max_branches": settings.max_branches,
            "max_tactics_per_state": settings.max_tactics_per_state,
            "max_repair_attempts": settings.max_repair_attempts,
            "max_total_tactics": settings.max_total_tactics,
            "max_seconds": settings.max_seconds_per_theorem,
            "max_stagnant_steps": settings.max_stagnant_steps,
        }
    if max_depth is not None:
        data["max_depth"] = max_depth
    if max_branches is not None:
        data["max_branches"] = max_branches
    if max_seconds is not None:
        data["max_seconds"] = max_seconds
    return SearchBudget(**data)


@app.command("list-theorems")
def list_theorems(verbose: bool = typer.Option(False, "--verbose")):
    backend = make_backend()
    if verbose and hasattr(backend, "list_theorem_infos"):
        infos = backend.list_theorem_infos()  # type: ignore[attr-defined]
        for idx, info in enumerate(infos):
            typer.echo(str(info.get("name", "")))
            typer.echo(f"file: {info.get('file')}")
            typer.echo(f"line: {info.get('line')}")
            typer.echo(f"kind: {info.get('kind')}")
            typer.echo(f"statement: {info.get('statement')}")
            if idx != len(infos) - 1:
                typer.echo("")
        return
    for name in backend.list_theorems():
        typer.echo(name)


@app.command("run")
def run(
    theorem: str = typer.Option(..., "--theorem", "-t"),
    max_depth: Optional[int] = typer.Option(None),
    max_branches: Optional[int] = typer.Option(None),
    max_seconds: Optional[float] = typer.Option(None),
    budget_profile: Optional[str] = typer.Option(
        None, "--budget-profile", help="tiny, starter, wide, deep, aggressive"
    ),
    print_trace: bool = typer.Option(False),
):
    engine = make_engine()
    result = engine.run(
        theorem, make_budget(max_depth, max_branches, max_seconds, budget_profile)
    )
    typer.echo(f"theorem: {result.theorem_name}")
    typer.echo(f"status: {result.status}")
    typer.echo(f"solved: {result.solved}")
    typer.echo(f"proof: {result.proof}")
    typer.echo(f"branches_explored: {result.branches_explored}")
    typer.echo(f"branches_pruned: {result.branches_pruned}")
    typer.echo(f"tactics_attempted: {result.tactics_attempted}")
    typer.echo(f"repair_attempts: {result.repair_attempts}")
    typer.echo(f"repair_successes: {result.repair_successes}")
    if result.error:
        typer.echo(f"error: {result.error}")
    if print_trace:
        typer.echo(json.dumps(result.trace, indent=2, ensure_ascii=False))


@app.command("eval")
def eval_cmd(json_output: bool = typer.Option(False, "--json")):
    engine = make_engine()
    results, metrics = run_starter_eval(engine)
    payload = {
        "results": [r.model_dump() for r in results],
        "metrics": metrics.model_dump(),
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for result in results:
        typer.echo(
            f"{result.theorem_name}: {result.status} solved={result.solved} proof={result.proof}"
        )
    typer.echo("metrics:")
    for k, v in metrics.model_dump().items():
        typer.echo(f"  {k}: {v}")


@app.command("budget-sweep")
def budget_sweep(json_output: bool = typer.Option(False, "--json")):
    engine = make_engine()
    payload = run_budget_sweep(engine)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    for profile, data in payload.items():
        metrics = data["metrics"]
        typer.echo(
            f"{profile}: score={metrics['score']:.3f} completion={metrics['proof_completion_rate']:.3f} budget_failures={metrics['budget_failure_rate']:.3f}"
        )


@app.command("trace-summary")
def trace_summary(path: Optional[Path] = typer.Option(None, "--path")):
    settings = load_settings()
    payload = summarize_trace_file(path or settings.trace_path)
    typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))


@app.command("trace-analytics")
def trace_analytics(path: Optional[Path] = typer.Option(None, "--path")):
    settings = load_settings()
    records = load_trace_records(path or settings.trace_path)
    typer.echo(json.dumps(analyze_records(records), indent=2, ensure_ascii=False))


@app.command("validate-traces")
def validate_traces(
    input: Path = typer.Option(..., "--input"),
    strict: bool = typer.Option(False, "--strict"),
    json_output: bool = typer.Option(False, "--json"),
):
    payload = validate_trace_file(input, strict=strict)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        typer.echo(f"ok: {payload['ok']}")
        typer.echo(f"records_total: {payload['records_total']}")
        typer.echo(f"records_valid: {payload['records_valid']}")
        typer.echo(f"records_invalid: {payload['records_invalid']}")
        typer.echo(f"legacy_records: {payload['legacy_records']}")
        if payload.get("note"):
            typer.echo(payload["note"])
        for err in payload.get("errors", [])[:10]:
            location = f"line {err.get('line')}"
            event_index = err.get("event_index")
            if event_index is not None:
                location += f", event {event_index}"
            typer.echo(f"{location}: {err.get('message')}")
    if not payload["ok"]:
        raise typer.Exit(code=1)


@app.command("trace-validate")
def trace_validate_alias(
    path: Path = typer.Option(..., "--path"),
    strict: bool = typer.Option(False, "--strict"),
    json_output: bool = typer.Option(False, "--json"),
):
    validate_traces(input=path, strict=strict, json_output=json_output)


@app.command("migrate-traces")
def migrate_traces(
    input: Path = typer.Option(..., "--input"),
    output: Path = typer.Option(..., "--output"),
    json_output: bool = typer.Option(False, "--json"),
):
    payload = migrate_trace_file(input, output)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        typer.echo(f"ok: {payload['ok']}")
        typer.echo(f"input: {payload['input']}")
        typer.echo(f"output: {payload['output']}")
        typer.echo(f"records_total: {payload['records_total']}")
        typer.echo(f"records_migrated: {payload['records_migrated']}")
        typer.echo(f"records_invalid: {payload['records_invalid']}")
        for err in payload.get("errors", [])[:10]:
            typer.echo(f"line {err.get('line')}: {err.get('error')}")
    if not payload["ok"]:
        raise typer.Exit(code=1)


@app.command("trace-migrate")
def trace_migrate_alias(
    input: Path = typer.Option(..., "--input"),
    output: Path = typer.Option(..., "--output"),
    json_output: bool = typer.Option(False, "--json"),
):
    migrate_traces(input=input, output=output, json_output=json_output)


@app.command("dashboard")
def dashboard(
    path: Optional[Path] = typer.Option(None, "--path"),
    output: Path = typer.Option(Path(".runs/dashboard.html"), "--output", "-o"),
):
    settings = load_settings()
    generated = render_html_dashboard(path or settings.trace_path, output)
    typer.echo(str(generated))


@app.command("trace-dot")
def trace_dot(
    index: int = typer.Option(
        -1, "--index", help="Trace record index. -1 means latest."
    ),
    path: Optional[Path] = typer.Option(None, "--path"),
):
    settings = load_settings()
    records = load_trace_records(path or settings.trace_path)
    if not records:
        raise typer.BadParameter("No trace records found.")
    typer.echo(proof_tree_dot(records[index]))


@app.command("doctor")
def doctor(json_output: bool = typer.Option(False, "--json")):
    payload = run_doctor(load_settings())
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    typer.echo(f"ok: {payload['ok']}")
    typer.echo(f"backend: {payload['backend']}")
    typer.echo("backend availability:")
    for name, status in payload.get("backend_availability", {}).items():
        available = "available" if status.get("available") else "unavailable"
        typer.echo(f"- {name}: {available} ({status.get('reason')})")
    for check in payload["checks"]:
        if check["ok"]:
            mark = "OK"
        elif check["severity"] == "warning":
            mark = "WARN"
        else:
            mark = "FAIL"
        typer.echo(f"{mark} [{check['severity']}] {check['name']}: {check['detail']}")
    typer.echo("ecosystem:")
    for name, status in payload.get("ecosystem", {}).items():
        typer.echo(f"- {name}: {status.get('status')} ({status.get('detail')})")
    typer.echo(payload["next_action"])


@app.command("ecosystem-status")
def ecosystem_status(json_output: bool = typer.Option(False, "--json")):
    settings = load_settings()
    repo_root = Path(__file__).resolve().parents[2]
    copilot_docs_present = (
        repo_root / "docs" / "integrations" / "leancopilot_bridge.md"
    ).exists()
    leanagent_docs_present = (
        repo_root / "docs" / "integrations" / "leanagent_lifelong_learning.md"
    ).exists()
    adapter = LeanDojoV2Client(
        repo=settings.leandojo_repo,
        commit=settings.leandojo_commit,
        theorem_filter=settings.leandojo_theorem_filter,
        import_module=settings.leandojo_import_module,
    )
    adapter_status = adapter.dependency_status()
    payload = {
        "LeanDojo-v2": {
            "role": "core backend target",
            "adapter": "present",
            "configured": bool(settings.leandojo_repo),
            "repo": settings.leandojo_repo,
            "commit": settings.leandojo_commit,
            "theorem_filter": settings.leandojo_theorem_filter,
            "dependency": adapter_status,
        },
        "LeanCopilot": {
            "role": "future editor/copilot bridge",
            "status": "docs present" if copilot_docs_present else "docs missing",
        },
        "LeanAgent": {
            "role": "future lifelong learning layer",
            "status": "docs present" if leanagent_docs_present else "docs missing",
        },
        "Legacy LeanDojo": {
            "role": "deprecated/reference only",
        },
        "TorchLean": {
            "role": "research-only for ML verification",
            "status": "not part of theorem-proving core",
        },
        "BRIDGE": {
            "role": "skipped unless code becomes useful",
        },
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    typer.echo(
        "LeanDojo-v2: core backend target, adapter present, "
        + ("configured" if payload["LeanDojo-v2"]["configured"] else "unconfigured")
    )
    typer.echo(
        "  dependency: "
        + ("available" if adapter_status.get("available") else "unavailable")
        + f" ({adapter_status.get('reason')})"
    )
    typer.echo(
        "LeanCopilot: future editor/copilot bridge, "
        + ("docs present" if copilot_docs_present else "docs missing")
    )
    typer.echo(
        "LeanAgent: future lifelong learning layer, "
        + ("docs present" if leanagent_docs_present else "docs missing")
    )
    typer.echo("Legacy LeanDojo: deprecated/reference only")
    typer.echo(
        "TorchLean: research-only for ML verification, not part of theorem-proving core"
    )
    typer.echo("BRIDGE: skipped unless code becomes useful")


@app.command("trace-export-dspy")
def trace_export_dspy(
    path: Optional[Path] = typer.Option(None, "--path"),
    output: Path = typer.Option(Path(".runs/dspy_examples.jsonl"), "--output", "-o"),
    include_failures: bool = typer.Option(False, "--include-failures"),
    no_repairs: bool = typer.Option(False, "--no-repairs"),
    json_output: bool = typer.Option(False, "--json"),
):
    settings = load_settings()
    trace_path = path or settings.trace_path
    generated = write_training_jsonl(
        trace_path,
        output,
        include_failures=include_failures,
        include_repairs=not no_repairs,
    )
    examples = extract_training_examples(
        load_trace_records(trace_path),
        include_failures=include_failures,
        include_repairs=not no_repairs,
    )
    summary = summarize_training_examples(examples)
    payload = {"output": str(generated), "summary": summary}
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    typer.echo(f"wrote: {generated}")
    typer.echo(json.dumps(summary, indent=2, ensure_ascii=False))


@app.command("replay")
def replay(
    index: int = typer.Option(
        -1, "--index", help="Trace record index. -1 means latest."
    ),
    theorem: Optional[str] = typer.Option(
        None,
        "--theorem",
        help="Replay this theorem from trace file; defaults to selected trace record.",
    ),
    verify_with_lean: bool = typer.Option(False, "--verify-with-lean"),
    path: Optional[Path] = typer.Option(None, "--path"),
    json_output: bool = typer.Option(False, "--json"),
):
    settings = load_settings()
    records = load_trace_records(path or settings.trace_path)
    if not records:
        raise typer.BadParameter("No trace records found.")
    record = records[index]
    theorem_name = theorem or record.get("theorem_name")
    proof = record.get("proof", [])
    if not theorem_name:
        raise typer.BadParameter("No theorem name found in selected trace record.")
    payload = replay_proof(
        make_backend(), theorem_name, proof, verify_with_lean=verify_with_lean
    )
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    typer.echo(f"theorem: {payload['theorem_name']}")
    typer.echo(f"valid: {payload['valid']}")
    typer.echo(f"solved: {payload['solved']}")
    if payload.get("failed_step"):
        typer.echo(f"failed_step: {payload['failed_step']}")
    for event in payload["events"]:
        typer.echo(
            f"{event['step']}. {event['tactic']} accepted={event['accepted']} solved={event['solved']}"
        )
    if verify_with_lean and payload.get("verification") is not None:
        typer.echo(f"verification: {payload['verification']}")


@app.command("experiment-grid")
def experiment_grid(
    budget_profiles: str = typer.Option(
        "tiny,starter", "--budget-profiles", help="Comma-separated profile names."
    ),
    retrieval_modes: str = typer.Option(
        "bm25,semantic", "--retrieval-modes", help="Comma-separated retrieval modes."
    ),
    json_output: bool = typer.Option(False, "--json"),
):
    settings = load_settings()
    profiles = [p.strip() for p in budget_profiles.split(",") if p.strip()]
    modes = [m.strip() for m in retrieval_modes.split(",") if m.strip()]

    def factory(profile: str, mode: str):
        lean_file = None
        if settings.backend == "lean_cli":
            lean_file = str(settings.lean_project_root / settings.lean_file)
        return ProofSearchEngine(
            backend=make_backend(),
            proposer=make_proposer(),
            repairer=make_repairer(),
            retriever=PremiseRetriever.from_mode(
                mode,
                top_k=settings.retrieval_top_k,
                lean_file=lean_file,
                embedding_model=settings.embedding_model,
            ),
            trace_store=TraceStore(settings.trace_path),
        )

    payload = run_experiment_grid(
        factory, budget_profiles=profiles, retrieval_modes=modes
    )
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    for mode, by_profile in payload.items():
        typer.echo(f"retrieval={mode}")
        for profile, data in by_profile.items():
            metrics = data["metrics"]
            typer.echo(
                f"  {profile}: score={metrics['score']:.3f} completion={metrics['proof_completion_rate']:.3f} accept={metrics['tactic_accept_rate']:.3f}"
            )


@app.command("failure-report")
def failure_report(
    path: Optional[Path] = typer.Option(None, "--path"),
    group_by: str = typer.Option("category", "--group-by", help="category|theorem"),
    json_output: bool = typer.Option(False, "--json"),
):
    settings = load_settings()
    records = load_trace_records(path or settings.trace_path)
    payload = classify_records(records)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    typer.echo(f"runs: {payload['runs']}")
    if group_by == "theorem":
        typer.echo("by_theorem:")
        for theorem, stats in payload.get("by_theorem", {}).items():
            typer.echo(
                f"  {theorem}: runs={stats.get('runs')} by_category={stats.get('by_category')}"
            )
    else:
        typer.echo(f"by_category: {payload['by_category']}")
    for item in payload["records"]:
        typer.echo(
            f"{item.get('theorem_name')}: {item['category']} [{item['severity']}] - {item['action']}"
        )


@app.command("compare-traces")
def compare_traces(
    left: Path = typer.Option(..., "--left"),
    right: Path = typer.Option(..., "--right"),
    left_label: str = typer.Option("left", "--left-label"),
    right_label: str = typer.Option("right", "--right-label"),
    json_output: bool = typer.Option(False, "--json"),
):
    payload = compare_trace_sets(
        load_trace_records(left),
        load_trace_records(right),
        left_label=left_label,
        right_label=right_label,
    )
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    typer.echo(
        f"{left_label}: completion={payload['left']['completion_rate']:.3f} accept={payload['left']['tactic_accept_rate']:.3f}"
    )
    typer.echo(
        f"{right_label}: completion={payload['right']['completion_rate']:.3f} accept={payload['right']['tactic_accept_rate']:.3f}"
    )
    typer.echo("delta_right_minus_left:")
    for key, value in payload["delta_right_minus_left"].items():
        typer.echo(f"  {key}: {value}")


@app.command("pack-dataset")
def pack_dataset(
    path: Optional[Path] = typer.Option(None, "--path"),
    output_dir: Path = typer.Option(Path(".runs/dataset_pack"), "--output-dir", "-o"),
    include_failures: bool = typer.Option(False, "--include-failures"),
    no_repairs: bool = typer.Option(False, "--no-repairs"),
    min_quality: str = typer.Option("any", "--min-quality"),
    dev_ratio: float = typer.Option(0.2, "--dev-ratio"),
    json_output: bool = typer.Option(False, "--json"),
):
    settings = load_settings()
    payload = build_dataset_pack(
        path or settings.trace_path,
        output_dir,
        include_failures=include_failures,
        include_repairs=not no_repairs,
        min_quality=min_quality,
        dev_ratio=dev_ratio,
    )
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    typer.echo(f"dataset: {output_dir}")
    typer.echo(f"train_examples: {payload['train_examples']}")
    typer.echo(f"dev_examples: {payload['dev_examples']}")


@app.command("snapshot-config")
def snapshot_config(
    output: Path = typer.Option(Path(".runs/config_snapshot.json"), "--output", "-o"),
    json_output: bool = typer.Option(False, "--json"),
):
    settings = load_settings()
    generated = write_config_snapshot(settings, output)
    payload = json.loads(generated.read_text(encoding="utf-8"))
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    typer.echo(str(generated))


if __name__ == "__main__":
    app()
