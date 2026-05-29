"""Module that contains tests for the module that contains implementation of the logger."""

from __future__ import annotations

import typing

import pytest

from uv_upsync import logging


if typing.TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_logger_is_singleton() -> None:
    logger1 = logging.Logger()
    logger2 = logging.Logger()
    assert logger1 is logger2


def test_logger_singleton_reset() -> None:
    logger1 = logging.Logger()
    logging.Logger._instance = None
    logger2 = logging.Logger()
    assert logger1 is not logger2


def test_configure_sets_state() -> None:
    logger = logging.Logger()
    logger.configure(quiet=True, verbose=True, color=False)

    assert logger.quiet is True
    assert logger.verbose is True
    assert logger.color is False


def test_status_outputs_verb_and_message(mocker: MockerFixture) -> None:
    mock_echo = mocker.patch("click.echo")

    logger = logging.Logger()
    logger.status("Resolved", "7 packages in 12ms")

    mock_echo.assert_called_once()
    message = mock_echo.call_args[0][0]
    assert "Resolved" in message
    assert "7 packages in 12ms" in message


def test_status_suppressed_when_quiet(mocker: MockerFixture) -> None:
    mock_echo = mocker.patch("click.echo")

    logger = logging.Logger()
    logger.configure(quiet=True)
    logger.status("Resolved", "nothing")

    mock_echo.assert_not_called()


def test_update_renders_version_diff(mocker: MockerFixture) -> None:
    mock_echo = mocker.patch("click.echo")

    logger = logging.Logger()
    logger.update("httpx", "0.27.0", "0.28.1")

    message = mock_echo.call_args[0][0]
    assert "Updated" in message
    assert "v0.27.0" in message
    assert "v0.28.1" in message


def test_update_suppressed_when_quiet(mocker: MockerFixture) -> None:
    mock_echo = mocker.patch("click.echo")

    logger = logging.Logger()
    logger.configure(quiet=True)
    logger.update("httpx", "0.27.0", "0.28.1")

    mock_echo.assert_not_called()


@pytest.mark.parametrize(
    ("quiet", "verbose", "expected_calls"),
    [
        (False, False, 0),
        (False, True, 1),
        (True, True, 0),
    ],
)
def test_skip_requires_verbose(
    mocker: MockerFixture,
    *,
    quiet: bool,
    verbose: bool,
    expected_calls: int,
) -> None:
    mock_echo = mocker.patch("click.echo")

    logger = logging.Logger()
    logger.configure(quiet=quiet, verbose=verbose)
    logger.skip("Skipping something")

    assert mock_echo.call_count == expected_calls


@pytest.mark.parametrize(("method", "prefix"), [("warning", "warning:"), ("error", "error:")])
def test_warning_and_error_go_to_stderr(
    mocker: MockerFixture,
    method: str,
    prefix: str,
) -> None:
    mock_echo = mocker.patch("click.echo")

    logger = logging.Logger()
    getattr(logger, method)("something happened")

    message = mock_echo.call_args[0][0]
    assert prefix in message
    assert "something happened" in message
    assert mock_echo.call_args[1]["err"] is True


def test_echo_passes_configured_color(mocker: MockerFixture) -> None:
    mock_echo = mocker.patch("click.echo")

    logger = logging.Logger()
    logger.configure(color=True)
    logger.status("Resolved", "x")

    assert mock_echo.call_args[1]["color"] is True
