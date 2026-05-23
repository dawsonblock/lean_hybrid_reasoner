import json

from pathlib import Path

from lean_hybrid_reasoner.traces.migrate import migrate_trace_file
from lean_hybrid_reasoner.traces.validate import validate_trace_file


def test_migrate_traces_upgrades_legacy_record(tmp_path: Path):
    src = tmp_path / "legacy.jsonl"
    dst = tmp_path / "migrated.jsonl"
    legacy = {
        "theorem_name": "demo",
        "solved": False,
        "status": "failed",
        "trace": [
            {"event": "start", "theorem": "demo"},
            {
                "event": "execute_tactic",
                "branch_id": "root",
                "tactic": "simp",
                "accepted": False,
                "solved": False,
                "error": "unknown identifier",
            },
        ],
    }
    src.write_text(json.dumps(legacy) + "\n", encoding="utf-8")

    migrate_payload = migrate_trace_file(src, dst)
    assert migrate_payload["ok"] is True
    assert migrate_payload["records_migrated"] == 1

    strict_payload = validate_trace_file(dst, strict=True)
    assert strict_payload["ok"] is True
    assert strict_payload["records_valid"] == 1
