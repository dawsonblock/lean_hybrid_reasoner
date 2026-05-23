from lean_hybrid_reasoner.config.snapshot import (
    build_config_snapshot,
    write_config_snapshot,
)
from lean_hybrid_reasoner.settings import Settings


def test_config_snapshot_contains_settings(tmp_path):
    settings = Settings(backend="mock", trace_path=tmp_path / "traces.jsonl")
    payload = build_config_snapshot(settings)
    assert payload["schema_version"] == "0.6"
    assert payload["settings"]["backend"] == "mock"
    path = write_config_snapshot(settings, tmp_path / "snapshot.json")
    assert path.exists()
