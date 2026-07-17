"""Module that contains a `click.Command` whose help mirrors uv's clap output."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click


if TYPE_CHECKING:
    from collections.abc import Iterable


class HelpFormatter(click.HelpFormatter):
    def write_usage(self, prog: str, args: str = "", prefix: str | None = None) -> None:
        if prefix is None:
            prefix = click.style("Usage: ", bold=True)
        super().write_usage(prog, args, prefix)

    def write_heading(self, heading: str) -> None:
        self.write(click.style(f"{heading}:\n", bold=True))

    def write_dl(
        self,
        rows: Iterable[tuple[str, str]],
        col_max: int = 30,
        col_spacing: int = 2,
    ) -> None:
        colored_rows = [(click.style(name, fg="cyan", bold=True), text) for name, text in rows]
        super().write_dl(colored_rows, col_max, col_spacing)


class Command(click.Command):
    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        self.format_usage(ctx, formatter)
        self.format_help_text(ctx, formatter)
        self.format_options(ctx, formatter)
        self.format_epilog(ctx, formatter)

    def get_help(self, ctx: click.Context) -> str:
        formatter = HelpFormatter(width=ctx.terminal_width, max_width=ctx.max_content_width)
        self.format_help(ctx, formatter)
        return formatter.getvalue()
