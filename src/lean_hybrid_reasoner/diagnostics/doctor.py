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
    lean_file = settings.lean_file if settings.lean_file.is_absolute() else project_root / settings.lean_file

    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: Any = None, severity: str = "error") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail, "severity": severity})

    add("backend_supported", settings.backend in {"mock", "lean_cli"}, settings.backend)
    add("trace_path_writable", _path_writable(settings.trace_path), str(settings.trace_path))
    add("lake_on_path", lake is not None, lake, severity="warning")
    add("lean_on_path", lean is not None, lean, severity="warning")

    if settings.backend == "lean_cli":
        add("lean_project_root_exists", project_root.exists(), str(project_root))
        add("lean_file_exists", lean_file.exists(), str(lean_file))
        add("lean_timeout_positive", settings.lean_timeout_seconds > 0, settings.lean_timeout_seconds)
        add("lean_or_lake_available", bool(lake or lean), {"lake": lake, "lean": lean})
    else:
        add("mock_backend_ready", True, "mock backend needs no Lean install", severity="info")

    add("dspy_available", _module_available("dspy"), "pip install -e .[llm]", severity="warning")
    add("langgraph_available", _module_available("langgraph"), "pip install -e .[llm]", severity="warning")
    add("sentence_transformers_available", _module_available("sentence_transformers"), "pip install -e .[semantic]", severity="warning")
    add("faiss_available", _module_available("faiss") or _module_available("faiss_cpu"), "pip install -e .[semantic]", severity="warning")

    required_failed = [c for c in checks if not c["ok"] and c["severity"] == "error"]
    warning_failed = [c for c in checks if not c["ok"] and c["severity"] == "warning"]

    return {
        "ok": not required_failed,
        "backend": settings.backend,
        "cwd": os.getcwd(),
        "checks": checks,
        "required_failures": len(required_failed),
        "warnings": len(warning_failed),
        "next_action": "Fix required failures first; warnings only matter for optional integrations." if required_failed or warning_failed else "Environment looks ready.",
    }
