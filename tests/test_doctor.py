from lean_hybrid_reasoner.diagnostics.doctor import run_doctor
from lean_hybrid_reasoner.settings import Settings


def test_doctor_mock_backend_is_ok(tmp_path):
    settings = Settings(backend="mock", trace_path=tmp_path / "traces.jsonl")
    payload = run_doctor(settings)
    assert payload["ok"] is True
    assert any(c["name"] == "mock_backend_ready" and c["ok"] for c in payload["checks"])
