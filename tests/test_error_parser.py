from lean_hybrid_reasoner.lean_backend.error_parser import parse_lean_error


def test_error_parser_unknown_identifier():
    parsed = parse_lean_error("unknown identifier 'Foo.bar'")
    assert parsed.category == "unknown_identifier"
    assert parsed.retryable is True


def test_error_parser_none():
    parsed = parse_lean_error(None)
    assert parsed.category == "none"
    assert parsed.retryable is False
