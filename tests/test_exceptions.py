"""Module that contains tests for the module that contains implementation of the exceptions."""

from __future__ import annotations

import pytest

from uv_plugin_up import exceptions


@pytest.mark.parametrize(
    "exception_class",
    [
        exceptions.BaseError,
        exceptions.InvalidDependencySpecifierError,
        exceptions.NoOperatorFoundError,
        exceptions.MultipleOperatorsFoundError,
        exceptions.UVCommandError,
    ],
)
def test_exceptions_inherit_from_base_error(exception_class: type[exceptions.BaseError]) -> None:
    assert issubclass(exception_class, exceptions.BaseError)


def test_base_error_is_exception() -> None:
    assert issubclass(exceptions.BaseError, Exception)


@pytest.mark.parametrize(
    ("dependency_specifier", "expected_message"),
    [
        ("invalid^1.0.0", "Invalid dependency specifier: 'invalid^1.0.0'"),
        ("package@latest", "Invalid dependency specifier: 'package@latest'"),
        ("pkg:1.0.0", "Invalid dependency specifier: 'pkg:1.0.0'"),
    ],
)
def test_invalid_dependency_specifier_error(
    dependency_specifier: str,
    expected_message: str,
) -> None:
    error = exceptions.InvalidDependencySpecifierError(dependency_specifier)
    assert str(error) == expected_message


@pytest.mark.parametrize(
    ("dependency_specifier", "expected_message"),
    [
        ("package", "No operator found in dependency specifier: 'package'"),
        ("some-pkg", "No operator found in dependency specifier: 'some-pkg'"),
        ("another_package", "No operator found in dependency specifier: 'another_package'"),
    ],
)
def test_no_operator_found_error(dependency_specifier: str, expected_message: str) -> None:
    error = exceptions.NoOperatorFoundError(dependency_specifier)
    assert str(error) == expected_message


@pytest.mark.parametrize(
    ("dependency_specifier", "expected_message"),
    [
        (
            "package>=1.0,<2.0",
            "Multiple operators found in dependency specifier: 'package>=1.0,<2.0'",
        ),
        (
            "pkg>=1.0,<=2.0",
            "Multiple operators found in dependency specifier: 'pkg>=1.0,<=2.0'",
        ),
    ],
)
def test_multiple_operators_found_error(
    dependency_specifier: str,
    expected_message: str,
) -> None:
    error = exceptions.MultipleOperatorsFoundError(dependency_specifier)
    assert str(error) == expected_message


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
