"""
Module that renders update results as JSON or Markdown.

Text output is handled directly by the logger; this module produces the
machine-readable formats used for scripting and for GitHub Action pull request
bodies.
"""

from __future__ import annotations

import json

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Sequence

    from uv_upsync.parsers import Update


def render(output_format: str, updated: Sequence[Update], held_back: Sequence[Update]) -> str:
    """Render the applied and held-back updates in the requested format."""
    if output_format == "json":
        return _render_json(updated, held_back)
    return _render_markdown(updated, held_back)


def _entry(update: Update) -> dict[str, str]:
    return {
        "name": update.name,
        "group": update.group,
        "old": update.old_version,
        "new": update.new_version,
    }


def _render_json(updated: Sequence[Update], held_back: Sequence[Update]) -> str:
    payload = {
        "updated": [_entry(update) for update in updated],
        "held_back": [_entry(update) for update in held_back],
    }
    return json.dumps(payload, indent=2)


def _render_markdown(updated: Sequence[Update], held_back: Sequence[Update]) -> str:
    lines: list[str] = []

    if updated:
        lines.append("### Updated dependencies")
        lines.append("")
        lines.extend(
            f"- ⬆️ `{update.name}` {update.old_version} → {update.new_version} ({update.group})"
            for update in updated
        )
    else:
        lines.append("No dependencies were updated.")

    if held_back:
        lines.append("")
        lines.append("### Held back")
        lines.append("")
        lines.extend(
            f"- `{update.name}` {update.old_version} → {update.new_version} ({update.group})"
            for update in held_back
        )

    return "\n".join(lines)
