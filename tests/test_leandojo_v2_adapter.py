from __future__ import annotations

from lean_hybrid_reasoner.lean_backend.leandojo_v2_client import (
    LeanDojoV2Client,
    LeanDojoV2Unavailable,
)


def test_leandojo_v2_adapter_import_safe():
    adapter = LeanDojoV2Client()
    status = adapter.dependency_status()
    assert "available" in status
    assert "reason" in status
    assert "action" in status


def test_missing_dependency_raises_adapter_specific_error(monkeypatch):
    monkeypatch.setattr(
        LeanDojoV2Client,
        "_detect_dependency_available",
        staticmethod(lambda: False),
    )
    adapter = LeanDojoV2Client()
    try:
        adapter.list_theorems()
    except LeanDojoV2Unavailable:
        return
    assert False, "Expected LeanDojoV2Unavailable when dependency is missing"


def test_dependency_detected_without_repo_is_unconfigured(monkeypatch):
    monkeypatch.setattr(
        LeanDojoV2Client,
        "_detect_dependency_available",
        staticmethod(lambda: True),
    )
    adapter = LeanDojoV2Client(repo=None)
    status = adapter.dependency_status()
    assert status["available"] is False
    assert "not configured" in str(status["reason"])


def test_placeholder_adapter_fails_fast_until_runtime_wired(monkeypatch):
    monkeypatch.setattr(
        LeanDojoV2Client,
        "_detect_dependency_available",
        staticmethod(lambda: True),
    )
    adapter = LeanDojoV2Client(repo="demo/repo")
    status = adapter.dependency_status()
    assert status["available"] is False
    assert "not implemented" in str(status["reason"])

    try:
        adapter.list_theorems()
    except LeanDojoV2Unavailable:
        return
    assert (
        False
    ), "Expected fail-fast LeanDojoV2Unavailable while adapter is placeholder"


def test_import_module_override_is_reported_when_missing():
    adapter = LeanDojoV2Client(import_module="definitely_missing_module_name")
    status = adapter.dependency_status()
    assert status["available"] is False
    assert status["import_override"] == "definitely_missing_module_name"
    assert status["detected_module"] is None
