from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from lean_hybrid_reasoner.traces.analytics import analyze_records


def load_trace_records(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records.append(json.loads(line))
    return records


def summarize_trace_file(path: str | Path) -> dict[str, Any]:
    records = load_trace_records(path)
    solved = sum(1 for r in records if r.get("solved"))
    summary = {
        "runs": len(records),
        "solved": solved,
        "failed": len(records) - solved,
        "theorems": [r.get("theorem_name") for r in records],
        "tactics_attempted": sum(int(r.get("tactics_attempted", 0)) for r in records),
        "branches_explored": sum(int(r.get("branches_explored", 0)) for r in records),
        "branches_pruned": sum(int(r.get("branches_pruned", 0)) for r in records),
    }
    summary["analytics"] = analyze_records(records)
    return summary


def proof_tree_dot(result: dict[str, Any]) -> str:
    lines = ["digraph proof_tree {", "  rankdir=LR;", "  node [shape=box];"]
    seen_nodes = set()
    for event in result.get("trace", []):
        branch = event.get("branch_id")
        if not branch:
            continue
        if branch not in seen_nodes:
            label = f"{branch[:8]}\\n{event.get('event')}"
            lines.append(f'  "{branch}" [label="{label}"];')
            seen_nodes.add(branch)
        parent = event.get("parent_branch_id")
        if parent:
            lines.append(f'  "{parent}" -> "{branch}";')
    lines.append("}")
    return "\n".join(lines)


def render_html_dashboard(path: str | Path, output_path: str | Path) -> Path:
    records = load_trace_records(path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    details = []
    analytics = analyze_records(records)
    for idx, record in enumerate(records, start=1):
        theorem = html.escape(str(record.get("theorem_name", "")))
        status = html.escape(str(record.get("status", "")))
        solved = html.escape(str(record.get("solved", "")))
        proof = html.escape("\n".join(record.get("proof", [])))
        rows.append(
            f"<tr><td>{idx}</td><td>{theorem}</td><td>{status}</td><td>{solved}</td>"
            f"<td>{record.get('branches_explored', 0)}</td><td>{record.get('branches_pruned', 0)}</td><td>{record.get('tactics_attempted', 0)}</td></tr>"
        )
        trace_json = html.escape(json.dumps(record.get("trace", []), indent=2, ensure_ascii=False))
        run_analysis = html.escape(json.dumps(analytics["per_run"][idx - 1] if idx - 1 < len(analytics["per_run"]) else {}, indent=2, ensure_ascii=False))
        details.append(
            f"<section><h2>{idx}. {theorem}</h2><p><b>Status:</b> {status} | <b>Solved:</b> {solved}</p>"
            f"<h3>Proof</h3><pre>{proof}</pre><h3>Run analytics</h3><pre>{run_analysis}</pre><h3>Trace</h3><pre>{trace_json}</pre></section>"
        )

    summary = summarize_trace_file(path)
    document = f"""<!doctype html>
<html>
<head>
<meta charset=\"utf-8\" />
<title>Lean Hybrid Reasoner Trace Dashboard</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.35; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 2rem; }}
th, td {{ border: 1px solid #ddd; padding: 0.5rem; text-align: left; }}
pre {{ background: #f6f8fa; padding: 1rem; overflow: auto; }}
section {{ border-top: 2px solid #ddd; padding-top: 1rem; margin-top: 2rem; }}
.badge {{ display:inline-block; padding:0.2rem 0.45rem; background:#eee; border-radius:0.4rem; margin-right:0.25rem; }}
</style>
</head>
<body>
<h1>Lean Hybrid Reasoner Trace Dashboard</h1>
<h2>Summary</h2>
<pre>{html.escape(json.dumps(summary, indent=2, ensure_ascii=False))}</pre>
<table>
<thead><tr><th>#</th><th>Theorem</th><th>Status</th><th>Solved</th><th>Branches</th><th>Pruned</th><th>Tactics</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
{''.join(details)}
</body>
</html>
"""
    output_path.write_text(document, encoding="utf-8")
    return output_path
