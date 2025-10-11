"""Module that contains tests for the module that contains implementation of the uv commands."""

from __future__ import annotations

import typing
import subprocess

import pytest

from uv_plugin_up import exceptions
from uv_plugin_up import uv


if typing.TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_lock_success(mocker: MockerFixture) -> None:
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = mocker.Mock(returncode=0, stdout="", stderr="")

    uv.lock()

    mock_run.assert_called_once_with(
        ("uv", "lock"),
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    ("returncode", "stdout", "stderr"),
    [
        (1, "", "Error: Package not found"),
        (2, "Processing...", "Fatal error occurred"),
        (1, "Locking dependencies", "Conflict detected"),
        (127, "", "Command not found"),
    ],
)
def test_lock_failure(
    mocker: MockerFixture,
    returncode: int,
    stdout: str,
    stderr: str,
) -> None:
    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=returncode,
        cmd=["uv", "lock"],
        output=stdout,
        stderr=stderr,
    )

    with pytest.raises(exceptions.UVCommandError) as exc_info:
        uv.lock()

    error = exc_info.value
    assert error.command == ["uv", "lock"]
    assert error.returncode == returncode
    assert error.stdout == stdout
    assert error.stderr == stderr


def test_lock_command_structure(mocker: MockerFixture) -> None:
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = mocker.Mock(returncode=0)

    uv.lock()

    call_args = mock_run.call_args
    assert call_args[0][0] == ("uv", "lock")
    assert call_args[1]["check"] is True
    assert call_args[1]["capture_output"] is True
    assert call_args[1]["text"] is True


def test_lock_exception_chain(mocker: MockerFixture) -> None:
    original_error = subprocess.CalledProcessError(
        returncode=1,
        cmd=["uv", "lock"],
        output="out",
        stderr="err",
    )

    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = original_error

    with pytest.raises(exceptions.UVCommandError) as exc_info:
        uv.lock()

    assert exc_info.value.__cause__ is original_error
