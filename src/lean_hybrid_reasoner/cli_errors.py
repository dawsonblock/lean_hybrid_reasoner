from __future__ import annotations

import typer


class UserFacingCliError(Exception):
    exit_code: int = 2

    def __init__(self, message: str, *, exit_code: int | None = None):
        super().__init__(message)
        if exit_code is not None:
            self.exit_code = exit_code


class DSPyUnavailableError(UserFacingCliError):
    pass


class InvalidDatasetError(UserFacingCliError):
    pass


class InvalidCompiledProgramError(UserFacingCliError):
    pass


def raise_user_error(message: str, *, exit_code: int = 2) -> None:
    typer.echo(message)
    raise typer.Exit(code=exit_code)


def handle_cli_error(exc: Exception) -> None:
    if isinstance(exc, UserFacingCliError):
        raise_user_error(str(exc), exit_code=exc.exit_code)
        return
    if isinstance(exc, FileNotFoundError):
        raise_user_error(str(exc), exit_code=2)
        return
    if isinstance(exc, ValueError):
        raise_user_error(str(exc), exit_code=2)
        return
    raise exc
