"""Module that contains a uv-styled logger built on top of `click.echo`."""

from __future__ import annotations

import typing

import click


class Logger:
    """Singleton logger that mimics uv's terse, status-oriented output style."""

    _instance: typing.ClassVar[Logger | None] = None

    quiet: bool
    verbose: bool
    color: bool | None

    def __new__(cls) -> typing.Self:
        if cls._instance is None:
            instance = super().__new__(cls)
            instance.quiet = False
            instance.verbose = False
            instance.color = None
            cls._instance = instance
        return typing.cast("typing.Self", cls._instance)

    def configure(
        self,
        *,
        quiet: bool = False,
        verbose: bool = False,
        color: bool | None = None,
    ) -> None:
        self.quiet = quiet
        self.verbose = verbose
        self.color = color

    def status(self, verb: str, message: str) -> None:
        """Print a uv-style status line: a bold green verb followed by a message."""
        if self.quiet:
            return
        self._echo(f"{click.style(verb, fg='green', bold=True)} {message}")

    def update(self, name: str, old_version: str, new_version: str) -> None:
        """Print a uv-style version bump: `Updated <name> v<old> -> v<new>`."""
        if self.quiet:
            return
        arrow = click.style("->", dim=True)
        old = click.style(f"v{old_version}", fg="cyan")
        new = click.style(f"v{new_version}", fg="cyan")
        self._echo(f"{click.style('Updated', fg='green', bold=True)} {name} {old} {arrow} {new}")

    def skip(self, message: str) -> None:
        """Print a dimmed, verbose-only note about a skipped dependency."""
        if self.quiet or not self.verbose:
            return
        self._echo(click.style(message, dim=True))

    def warning(self, message: str) -> None:
        self._echo(f"{click.style('warning:', fg='yellow', bold=True)} {message}", err=True)

    def error(self, message: str, *, cause: object | None = None) -> None:
        self._echo(f"{click.style('error:', fg='red', bold=True)} {message}", err=True)
        if cause is None:
            return
        first, *rest = str(cause).splitlines() or [""]
        self._echo(click.style(f"  Caused by: {first}", dim=True), err=True)
        for line in rest:
            self._echo(click.style(f"             {line}", dim=True), err=True)

    def _echo(self, message: str, *, err: bool = False) -> None:
        click.echo(message, err=err, color=self.color)
