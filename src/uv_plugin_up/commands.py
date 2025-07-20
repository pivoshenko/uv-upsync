"""Module that contains custom implementation of the `click.Command` with enriched formatting."""

from __future__ import annotations

import click


class HelpFormatter(click.HelpFormatter):
    def write_usage(self, prog: str, args: str = "", prefix: str | None = None) -> None:
        match prefix:
            case None:
                prefix = click.style("Usage: ", fg="green", bold=True)
            case _:
                pass
        super().write_usage(prog, args, prefix)

    def write_heading(self, heading: str) -> None:
        self.write(click.style(f"{heading}:\n", fg="green", bold=True))

    def write_dl(  # type: ignore[override]
        self,
        rows: list[tuple[str, str]],
        col_max: int = 30,
        col_spacing: int = 2,
    ) -> None:
        colored_rows = []
        for option_name, help_text in rows:
            colored_option = click.style(option_name, fg="magenta", bold=True)
            colored_rows.append((colored_option, help_text))
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
