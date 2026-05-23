from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_NAMESPACE_RE = re.compile(r"^\s*namespace\s+([A-Za-z_][A-Za-z0-9_'.]*)\s*$")
_END_RE = re.compile(r"^\s*end\b\s*([A-Za-z_][A-Za-z0-9_'.]*)?\s*$")
_DECL_START_RE = re.compile(r"^\s*(theorem|lemma|example|def)\b")
_NAME_RE = re.compile(r"^\s*(theorem|lemma|def)\s+([A-Za-z_][A-Za-z0-9_']*)\b")
_ARG_RE = re.compile(r"\(([^()]+?:[^()]+?)\)")


@dataclass(frozen=True)
class LeanDeclaration:
    kind: str
    local_name: str | None
    qualified_name: str
    statement: str
    hypotheses: list[str]
    namespace: str | None
    file: str
    line: int
    start_index: int
    head_for_proof: str


def _extract_statement(head_no_assign: str, kind: str, local_name: str | None) -> str:
    body = head_no_assign.strip()
    if kind != "example" and local_name:
        prefix = f"{kind} {local_name}"
        if body.startswith(prefix):
            body = body[len(prefix) :].strip()
    elif kind == "example" and body.startswith("example"):
        body = body[len("example") :].strip()

    colon = body.rfind(" : ")
    if colon >= 0:
        return body[colon + 3 :].strip()
    parts = body.split(":")
    return parts[-1].strip() if len(parts) > 1 else body


def parse_lean_declarations(
    text: str, source_path: str | Path
) -> list[LeanDeclaration]:
    lines = text.splitlines()
    decls: list[LeanDeclaration] = []
    namespace_stack: list[str] = []

    i = 0
    while i < len(lines):
        raw = lines[i]

        namespace_match = _NAMESPACE_RE.match(raw)
        if namespace_match:
            namespace_stack.extend(namespace_match.group(1).split("."))
            i += 1
            continue

        end_match = _END_RE.match(raw)
        if end_match:
            name = end_match.group(1)
            if name:
                parts = name.split(".")
                if namespace_stack[-len(parts) :] == parts:
                    namespace_stack = namespace_stack[: -len(parts)]
                elif namespace_stack:
                    namespace_stack.pop()
            elif namespace_stack:
                namespace_stack.pop()
            i += 1
            continue

        start_match = _DECL_START_RE.match(raw)
        if not start_match:
            i += 1
            continue

        kind = start_match.group(1)
        start_index = i
        head_lines = [raw.strip()]
        while ":=" not in head_lines[-1] and i + 1 < len(lines):
            i += 1
            head_lines.append(lines[i].strip())

        head_text = " ".join(part for part in head_lines if part)
        head_no_assign = head_text.split(":=", 1)[0].strip()

        name_match = _NAME_RE.match(head_no_assign)
        local_name = name_match.group(2) if name_match else None
        ns = ".".join(namespace_stack) if namespace_stack else None
        if local_name:
            qualified = f"{ns}.{local_name}" if ns else local_name
        else:
            synthetic = f"example@L{start_index + 1}"
            qualified = f"{ns}.{synthetic}" if ns else synthetic

        statement = _extract_statement(head_no_assign, kind=kind, local_name=local_name)
        hypotheses = [m.group(1).strip() for m in _ARG_RE.finditer(head_no_assign)]

        decls.append(
            LeanDeclaration(
                kind=kind,
                local_name=local_name,
                qualified_name=qualified,
                statement=statement,
                hypotheses=hypotheses,
                namespace=ns,
                file=str(source_path),
                line=start_index + 1,
                start_index=start_index,
                head_for_proof=head_no_assign + " := by",
            )
        )
        i += 1

    return decls
