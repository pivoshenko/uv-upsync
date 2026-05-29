"""Module that contains tests for the module that contains implementation of the exceptions."""

from __future__ import annotations

import pytest

from uv_upsync import exceptions


@pytest.mark.parametrize(
    "exception_class",
    [
        exceptions.BaseError,
        exceptions.UVCommandError,
    ],
)
def test_exceptions_inherit_from_base_error(exception_class: type[exceptions.BaseError]) -> None:
    assert issubclass(exception_class, exceptions.BaseError)


def test_base_error_is_exception() -> None:
    assert issubclass(exceptions.BaseError, Exception)


@pytest.mark.parametrize(
    ("command", "returncode", "stdout", "stderr"),
    [
        (["uv", "lock"], 1, "", "Error occurred"),
        (["uv", "lock"], 2, "Some output", ""),
        (["uv", "lock"], 1, "Output text", "Error text"),
        (["uv", "sync"], 1, "", ""),
    ],
)
def test_uv_command_error(
    command: list[str],
    returncode: int,
    stdout: str,
    stderr: str,
) -> None:
    error = exceptions.UVCommandError(command, returncode, stdout, stderr)

    assert error.command == command
    assert error.returncode == returncode
    assert error.stdout == stdout
    assert error.stderr == stderr

    error_message = str(error)
    assert f"Command {command!r} returned non-zero exit status {returncode}" in error_message

    if stdout:
        assert "Stdout:" in error_message
        assert stdout in error_message
    if stderr:
        assert "Stderr:" in error_message
        assert stderr in error_message
