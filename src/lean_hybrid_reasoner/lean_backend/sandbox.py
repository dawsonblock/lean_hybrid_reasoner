from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def _env_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.lower() in {"1", "true", "yes", "on"}


class LeanSandbox:
    def __init__(
        self,
        *,
        timeout_seconds: float,
        keep_temp: bool = False,
        temp_dir: str | Path | None = None,
    ):
        self.timeout_seconds = timeout_seconds
        self.keep_temp = keep_temp
        self.temp_dir = Path(temp_dir) if temp_dir else None

    @classmethod
    def from_environment(cls, *, timeout_seconds: float) -> "LeanSandbox":
        keep_temp = _env_truthy(os.getenv("LHR_KEEP_LEAN_TEMP"))
        temp_dir_env = os.getenv("LHR_LEAN_TEMP_DIR")
        temp_dir = Path(temp_dir_env) if temp_dir_env else None
        return cls(
            timeout_seconds=timeout_seconds, keep_temp=keep_temp, temp_dir=temp_dir
        )

    def run(
        self, *, project_root: Path, source_file: Path, source_text: str
    ) -> subprocess.CompletedProcess[str]:
        root = project_root.resolve()
        keep = self.keep_temp

        base = self.temp_dir if self.temp_dir is not None else None
        if base is not None:
            base.mkdir(parents=True, exist_ok=True)
        work_dir = Path(
            tempfile.mkdtemp(prefix="lhr_lean_", dir=str(base) if base else None)
        )

        rel = source_file.name
        try:
            rel = str(source_file.resolve().relative_to(root))
        except Exception:
            rel = source_file.name

        temp_lean = work_dir / rel
        temp_lean.parent.mkdir(parents=True, exist_ok=True)
        if source_file.exists():
            shutil.copy2(source_file, temp_lean)
        temp_lean.write_text(source_text, encoding="utf-8")

        lake = shutil.which("lake")
        lean = shutil.which("lean")
        if lake is not None:
            cmd = [lake, "env", "lean", str(temp_lean)]
            cwd = root
        elif lean is not None:
            cmd = [lean, str(temp_lean)]
            cwd = root
        else:
            raise RuntimeError("Neither `lake` nor `lean` was found on PATH.")

        try:
            return subprocess.run(
                cmd,
                cwd=cwd,
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = (
                exc.stdout
                if isinstance(exc.stdout, str)
                else (exc.stdout or b"").decode(errors="ignore")
            )
            stderr = (
                exc.stderr
                if isinstance(exc.stderr, str)
                else (exc.stderr or b"").decode(errors="ignore")
            )
            return subprocess.CompletedProcess(
                cmd,
                returncode=124,
                stdout=stdout,
                stderr=(
                    stderr + f"\nLean CLI timeout after {self.timeout_seconds} seconds"
                ),
            )
        finally:
            if not keep:
                shutil.rmtree(work_dir, ignore_errors=True)
