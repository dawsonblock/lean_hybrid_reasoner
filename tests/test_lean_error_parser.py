from lean_hybrid_reasoner.lean_backend.error_parser import parse_lean_error


def test_parse_lean_error_extracts_position_and_unknown_identifier():
    msg = "Demo.lean:12:34: error: unknown identifier 'Foo.bar'"
    parsed = parse_lean_error(msg)
    assert parsed.category == "unknown_identifier"
    assert parsed.line == 12
    assert parsed.column == 34
    assert parsed.suggestion is not None


def test_parse_lean_error_maps_syntax_error():
    parsed = parse_lean_error("error: invalid syntax near tactic")
    assert parsed.category == "syntax_error"
    assert parsed.retryable is True


def test_parse_lean_error_maps_tactic_failed():
    parsed = parse_lean_error("tactic 'simp' failed")
    assert parsed.category == "tactic_failed"
