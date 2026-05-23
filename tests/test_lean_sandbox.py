from __future__ import annotations

import subprocess
from pathlib import Path

import lean_hybrid_reasoner.lean_backend.sandbox as sandbox_mod
from lean_hybrid_reasoner.lean_backend.sandbox import LeanSandbox


def test_sandbox_cleans_temp_dir_when_keep_disabled(tmp_path: Path, monkeypatch):
    source_file = tmp_path / "Demo.lean"
    source_file.write_text("theorem demo : True := by\n  trivial\n", encoding="utf-8")
    temp_root = tmp_path / "lean_temp"

    def fake_which(name: str):
        if name == "lake":
            return None
        if name == "lean":
            return "/usr/bin/lean"
        return None

    def fake_run(cmd, cwd, text, capture_output, timeout):
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(sandbox_mod.shutil, "which", fake_which)
    monkeypatch.setattr(sandbox_mod.subprocess, "run", fake_run)

    sandbox = LeanSandbox(timeout_seconds=5.0, keep_temp=False, temp_dir=temp_root)
    result = sandbox.run(
        project_root=tmp_path,
        source_file=source_file,
        source_text=source_file.read_text(encoding="utf-8"),
    )
    assert result.returncode == 0
    assert list(temp_root.glob("*")) == []


def test_sandbox_keeps_temp_dir_when_enabled(tmp_path: Path, monkeypatch):
    source_file = tmp_path / "Demo.lean"
    source_file.write_text("theorem demo : True := by\n  trivial\n", encoding="utf-8")
    temp_root = tmp_path / "lean_temp"

    def fake_which(name: str):
        if name == "lake":
            return None
        if name == "lean":
            return "/usr/bin/lean"
        return None

    def fake_run(cmd, cwd, text, capture_output, timeout):
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(sandbox_mod.shutil, "which", fake_which)
    monkeypatch.setattr(sandbox_mod.subprocess, "run", fake_run)

    sandbox = LeanSandbox(timeout_seconds=5.0, keep_temp=True, temp_dir=temp_root)
    result = sandbox.run(
        project_root=tmp_path,
        source_file=source_file,
        source_text=source_file.read_text(encoding="utf-8"),
    )
    assert result.returncode == 0
    kept = list(temp_root.glob("lhr_lean_*"))
    assert kept
