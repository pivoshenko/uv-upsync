"""Module that contains tests for the module that contains implementation of the logger."""

from __future__ import annotations

import typing

import pytest

from uv_plugin_up import logging


if typing.TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_logger_is_singleton() -> None:
    logger1 = logging.Logger()
    logger2 = logging.Logger()
    assert logger1 is logger2


def test_singleton_meta_instances() -> None:
    class TestClass1(metaclass=logging.SingletonMeta):
        pass

    class TestClass2(metaclass=logging.SingletonMeta):
        pass

    instance1a = TestClass1()
    instance1b = TestClass1()
    instance2a = TestClass2()
    instance2b = TestClass2()

    assert instance1a is instance1b
    assert instance2a is instance2b
    assert instance1a is not instance2a


@pytest.mark.parametrize(
    ("log_method", "message", "expected_color"),
    [
        ("info", "Information message", "green"),
        ("warning", "Warning message", "yellow"),
        ("error", "Error message", "red"),
    ],
)
def test_logger_methods(
    mocker: MockerFixture,
    log_method: str,
    message: str,
    expected_color: str,
) -> None:
    mock_echo = mocker.patch("click.echo")
    mock_style = mocker.patch("click.style", return_value=f"styled_{message}")

    logger = logging.Logger()
    getattr(logger, log_method)(message)

    mock_style.assert_called_once()
    assert mock_style.call_args[0][0] == message
    assert "fg" in mock_style.call_args[1]
    assert mock_style.call_args[1]["fg"] == expected_color
    mock_echo.assert_called_once_with(f"styled_{message}")


def test_logger_exception_method(mocker: MockerFixture) -> None:
    mock_echo = mocker.patch("click.echo")
    mock_style = mocker.patch("click.style", side_effect=lambda x, **kwargs: f"styled_{x}")  # noqa: ARG005

    logger = logging.Logger()
    test_exception = ValueError("Test error")
    logger.exception("Error occurred", test_exception)

    assert mock_echo.call_count == 2
    assert mock_style.call_count == 2


def test_logger_warning_styling(mocker: MockerFixture) -> None:
    mock_echo = mocker.patch("click.echo")
    mock_style = mocker.patch("click.style", return_value="styled_message")

    logger = logging.Logger()
    logger.warning("Warning message")

    mock_style.assert_called_once_with("Warning message", fg="yellow", dim=True)
    mock_echo.assert_called_once()


def test_logger_error_styling(mocker: MockerFixture) -> None:
    mock_echo = mocker.patch("click.echo")
    mock_style = mocker.patch("click.style", return_value="styled_message")

    logger = logging.Logger()
    logger.error("Error message")

    mock_style.assert_called_once_with("Error message", fg="red", bold=True)
    mock_echo.assert_called_once()


@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        ("info", ("test message",)),
        ("warning", ("test message",)),
        ("error", ("test message",)),
        ("exception", ("test message", Exception("error"))),
    ],
)
def test_all_logger_methods_call_log(
    mocker: MockerFixture,
    method_name: str,
    args: tuple[str, ...],
) -> None:
    mock_echo = mocker.patch("click.echo")
    mocker.patch("click.style", return_value="styled")

    logger = logging.Logger()
    getattr(logger, method_name)(*args)

    assert mock_echo.called
