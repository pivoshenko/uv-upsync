"""Module that contains tests for custom Click command formatting."""

from __future__ import annotations

import typing

import click
import pytest

from click.testing import CliRunner

from uv_upsync import commands


if typing.TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_help_formatter_inherits_from_click() -> None:
    assert issubclass(commands.HelpFormatter, click.HelpFormatter)


def test_command_inherits_from_click() -> None:
    assert issubclass(commands.Command, click.Command)


@pytest.mark.parametrize(
    ("prefix", "expected_styling"),
    [
        (None, True),
        ("Custom: ", False),
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


def test_help_formatter_write_heading(mocker: MockerFixture) -> None:
    mock_style = mocker.patch("click.style", return_value="styled_heading")

    formatter = commands.HelpFormatter()
    formatter.write_heading("Options")

    mock_style.assert_called_once()
    assert mock_style.call_args[0][0] == "Options:\n"
    assert mock_style.call_args[1] == {"bold": True}


def test_help_formatter_write_dl(mocker: MockerFixture) -> None:
    mock_style = mocker.patch("click.style", side_effect=lambda x, **_: f"styled_{x}")

    formatter = commands.HelpFormatter()
    formatter.write_dl([("--verbose", "Enable verbose output"), ("--quiet", "Quiet mode")])

    assert mock_style.call_count == 2
    for call in mock_style.call_args_list:
        assert call[1] == {"fg": "cyan", "bold": True}


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
