from __future__ import annotations

import pytest
import typer

from lean_hybrid_reasoner.cli_errors import (
    DSPyUnavailableError,
    handle_cli_error,
)


def test_handle_cli_error_raises_typer_exit():
    with pytest.raises(typer.Exit):
        handle_cli_error(DSPyUnavailableError("missing"))
