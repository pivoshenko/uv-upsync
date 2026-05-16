"""Module that contains implementation of the logger based on the `click.echo`."""

from __future__ import annotations

import typing

import click


class Logger:
    _instance: typing.ClassVar[Logger | None] = None

    def __new__(cls) -> typing.Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return typing.cast("typing.Self", cls._instance)

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
