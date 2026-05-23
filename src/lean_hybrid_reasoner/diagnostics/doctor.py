from __future__ import annotations

import importlib.util
import os
import shutil
from pathlib import Path
from typing import Any

from lean_hybrid_reasoner.settings import Settings


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _path_writable(path: Path) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        probe = path.parent / ".lhr_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def run_doctor(settings: Settings) -> dict[str, Any]:
    lake = shutil.which("lake")
    lean = shutil.which("lean")
    project_root = settings.lean_project_root
    lean_file = (
        settings.lean_file
        if settings.lean_file.is_absolute()
        else project_root / settings.lean_file
    )

    checks: list[dict[str, Any]] = []
    backend_availability: dict[str, dict[str, Any]] = {
        "mock": {"available": True, "reason": "built in"},
        "lean_cli": {
            "available": bool(lake or lean),
            "reason": "requires lean or lake executable",
            "lean": lean,
            "lake": lake,
        },
        "leandojo_v2": {
            "available": False,
            "reason": "adapter import check pending",
        },
    }

    def add(name: str, ok: bool, detail: Any = None, severity: str = "error") -> None:
        checks.append(
            {"name": name, "ok": bool(ok), "detail": detail, "severity": severity}
        )

    supported_backends = {"mock", "lean_cli", "leandojo", "leandojo_v2"}
    add("backend_supported", settings.backend in supported_backends, settings.backend)
    add(
        "trace_path_writable",
        _path_writable(settings.trace_path),
        str(settings.trace_path),
    )
    add("lake_on_path", lake is not None, lake, severity="warning")
    add("lean_on_path", lean is not None, lean, severity="warning")

    if settings.backend == "lean_cli":
        add("lean_project_root_exists", project_root.exists(), str(project_root))
        add("lean_file_exists", lean_file.exists(), str(lean_file))
        add(
            "lean_timeout_positive",
            settings.lean_timeout_seconds > 0,
            settings.lean_timeout_seconds,
        )
        add("lean_or_lake_available", bool(lake or lean), {"lake": lake, "lean": lean})
    elif settings.backend == "mock":
        add(
            "mock_backend_ready",
            True,
            "mock backend needs no Lean install",
            severity="info",
        )
    else:
        add(
            "leandojo_backend_selected",
            True,
            "LeanDojo-v2 backend selected; check adapter/dependency/config below",
            severity="info",
        )

    leandojo_detail: dict[str, Any]
    try:
        from lean_hybrid_reasoner.lean_backend.leandojo_v2_client import (
            LeanDojoV2Client,
        )

        adapter = LeanDojoV2Client(
            repo=settings.leandojo_repo,
            commit=settings.leandojo_commit,
            theorem_filter=settings.leandojo_theorem_filter,
        )
        status = adapter.dependency_status()
        leandojo_detail = {
            "available": bool(status.get("available")),
            "reason": status.get("reason"),
            "action": status.get("action"),
            "repo": settings.leandojo_repo,
            "commit": settings.leandojo_commit,
            "theorem_filter": settings.leandojo_theorem_filter,
        }
        backend_availability["leandojo_v2"] = {
            "available": bool(status.get("available")),
            "reason": status.get("reason"),
        }
        add(
            "leandojo_v2_adapter_import",
            True,
            "adapter present",
            severity="info",
        )
        add(
            "leandojo_v2_dependency_available",
            bool(status.get("available")),
            leandojo_detail,
            severity="warning",
        )
    except Exception as exc:
        leandojo_detail = {
            "available": False,
            "reason": f"adapter import failed: {exc}",
            "action": "check LeanDojo-v2 adapter installation",
            "repo": settings.leandojo_repo,
            "commit": settings.leandojo_commit,
            "theorem_filter": settings.leandojo_theorem_filter,
        }
        backend_availability["leandojo_v2"] = {
            "available": False,
            "reason": leandojo_detail["reason"],
        }
        add(
            "leandojo_v2_adapter_import",
            False,
            leandojo_detail["reason"],
            severity="warning",
        )

    add(
        "dspy_available",
        _module_available("dspy"),
        "pip install -e .[llm]",
        severity="warning",
    )
    add(
        "langgraph_available",
        _module_available("langgraph"),
        "pip install -e .[llm]",
        severity="warning",
    )
    add(
        "sentence_transformers_available",
        _module_available("sentence_transformers"),
        "pip install -e .[semantic]",
        severity="warning",
    )
    add(
        "faiss_available",
        _module_available("faiss") or _module_available("faiss_cpu"),
        "pip install -e .[semantic]",
        severity="warning",
    )

    ecosystem = {
        "LeanDojo-v2": {
            "status": "staged backend target",
            "adapter": "present",
            "configured": bool(settings.leandojo_repo),
            "detail": leandojo_detail,
        },
        "LeanCopilot": {
            "status": "future in-Lean bridge",
            "detail": "planned/documentation only",
        },
        "LeanAgent": {
            "status": "future lifelong learning layer",
            "detail": "planned/documentation only",
        },
    }

    required_failed = [c for c in checks if not c["ok"] and c["severity"] == "error"]
    warning_failed = [c for c in checks if not c["ok"] and c["severity"] == "warning"]

    return {
        "ok": not required_failed,
        "backend": settings.backend,
        "cwd": os.getcwd(),
        "backend_availability": backend_availability,
        "ecosystem": ecosystem,
        "checks": checks,
        "required_failures": len(required_failed),
        "warnings": len(warning_failed),
        "next_action": (
            "Fix required failures first; warnings only matter for optional integrations."
            if required_failed or warning_failed
            else "Environment looks ready."
        ),
    }
