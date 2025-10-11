"""Module that contains tests for custom Click command formatting."""

from __future__ import annotations

import typing

import click
import pytest

from click.testing import CliRunner

from uv_plugin_up import commands


if typing.TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_help_formatter_inherits_from_click() -> None:
    assert issubclass(commands.HelpFormatter, click.HelpFormatter)


def test_command_inherits_from_click() -> None:
    assert issubclass(commands.Command, click.Command)


@pytest.mark.parametrize(
    ("prefix", "expected_styling"),
    [
        (None, True),  # Should use default styled prefix
        ("Custom: ", False),  # Should use custom prefix as-is
    ],
)
def test_help_formatter_write_usage(
    mocker: MockerFixture,
    prefix: str | None,
    *,
    expected_styling: bool,
) -> None:
    mock_style = mocker.patch("click.style", return_value="styled_text")

    formatter = commands.HelpFormatter()
    formatter.write_usage("program", args="--help", prefix=prefix)

    if expected_styling:
        mock_style.assert_called()
    else:
        pass


def test_help_formatter_write_heading(mocker: MockerFixture) -> None:
    mock_style = mocker.patch("click.style", return_value="styled_heading")

    formatter = commands.HelpFormatter()
    formatter.write_heading("Options")

    mock_style.assert_called_once()
    assert mock_style.call_args[0][0] == "Options:\n"
    assert mock_style.call_args[1] == {"fg": "green", "bold": True}


@pytest.mark.parametrize(
    "rows",
    [
        [("--help", "Show help message")],
        [("--verbose", "Enable verbose output"), ("--quiet", "Quiet mode")],
        [("-v, --version", "Show version"), ("-h, --help", "Show help")],
    ],
)
def test_help_formatter_write_dl(mocker: MockerFixture, rows: list[tuple[str, str]]) -> None:
    mock_style = mocker.patch("click.style", side_effect=lambda x, **kwargs: f"styled_{x}")  # noqa: ARG005

    formatter = commands.HelpFormatter()
    formatter.write_dl(rows)

    assert mock_style.call_count == len(rows)
    for call in mock_style.call_args_list:
        assert call[1] == {"fg": "magenta", "bold": True}


def test_command_format_help_order(mocker: MockerFixture) -> None:
    cmd = commands.Command("test", callback=lambda: None)
    ctx = click.Context(cmd)
    formatter = commands.HelpFormatter()

    mock_usage = mocker.patch.object(cmd, "format_usage")
    mock_help_text = mocker.patch.object(cmd, "format_help_text")
    mock_options = mocker.patch.object(cmd, "format_options")
    mock_epilog = mocker.patch.object(cmd, "format_epilog")

    cmd.format_help(ctx, formatter)

    mock_usage.assert_called_once_with(ctx, formatter)
    mock_help_text.assert_called_once_with(ctx, formatter)
    mock_options.assert_called_once_with(ctx, formatter)
    mock_epilog.assert_called_once_with(ctx, formatter)


def test_command_get_help_returns_formatted_string() -> None:
    @click.command(cls=commands.Command)
    @click.option("--test", help="Test option")
    def test_command() -> None:
        """Test command description."""

    ctx = click.Context(test_command)
    help_text = test_command.get_help(ctx)

    assert isinstance(help_text, str)
    assert len(help_text) > 0
    assert "Test command description." in help_text


def test_command_integration_with_runner() -> None:
    @click.command(cls=commands.Command)
    @click.option("--name", default="World", help="Name to greet")
    def greet(name: str) -> None:
        """Greet someone."""
        click.echo(f"Hello {name}!")

    runner = CliRunner()
    result = runner.invoke(greet, ["--help"])

    assert result.exit_code == 0
    assert "Greet someone." in result.output


def test_help_formatter_default_prefix_styling(mocker: MockerFixture) -> None:
    mock_style = mocker.patch("click.style", return_value="Usage: ")

    formatter = commands.HelpFormatter()
    formatter.write_usage("program", args="[OPTIONS]", prefix=None)

    style_calls = [call for call in mock_style.call_args_list if "Usage: " in str(call)]
    assert len(style_calls) > 0
    assert any(call[1].get("fg") == "green" and call[1].get("bold") is True for call in style_calls)
