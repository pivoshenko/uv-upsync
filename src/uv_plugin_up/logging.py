"""Module that contains implementation of the logger based on the `click.echo`."""

from __future__ import annotations

import click


class Logger:
    def info(self, message: str) -> None:
        self._log(click.style(message, fg="green"))

    def warning(self, message: str) -> None:
        self._log(click.style(message, fg="yellow", dim=True))

    def exception(self, message: str, exception: Exception) -> None:
        self._log(click.style(message, fg="red", bold=True))
        self._log(click.style(str(exception), fg="red", dim=True))

    def error(self, message: str) -> None:
        self._log(click.style(message, fg="red", bold=True))

    def _log(self, message: str) -> None:
        click.echo(message)
