from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lean_hybrid_reasoner.settings import Settings


def _cmd_version(command: str, args: list[str]) -> dict[str, Any]:
    exe = shutil.which(command)
    if not exe:
        return {"available": False, "path": None, "version": None}
    try:
        completed = subprocess.run(
            [exe, *args], capture_output=True, text=True, timeout=5
        )
        text = (completed.stdout or completed.stderr or "").strip().splitlines()
        return {
            "available": True,
            "path": exe,
            "version": text[0] if text else "",
            "returncode": completed.returncode,
        }
    except Exception as exc:  # pragma: no cover - defensive environment probe
        return {"available": True, "path": exe, "version": None, "error": str(exc)}


def build_config_snapshot(settings: Settings) -> dict[str, Any]:
    lhr_env = {k: v for k, v in sorted(os.environ.items()) if k.startswith("LHR_")}
    return {
        "schema_version": "0.6",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "settings": settings.model_dump(mode="json"),
        "environment": lhr_env,
        "tools": {
            "lean": _cmd_version("lean", ["--version"]),
            "lake": _cmd_version("lake", ["--version"]),
        },
    }


def write_config_snapshot(settings: Settings, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(build_config_snapshot(settings), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output
