"""Module that contains tests for the JSON and Markdown renderers."""

from __future__ import annotations

import json

from uv_upsync import report
from uv_upsync.parsers import Update


def _update(name: str, old: str, new: str, group: str = "project") -> Update:
    return Update(group=group, index=0, name=name, old_version=old, new_version=new, new_text="")


def test_render_json() -> None:
    updated = [_update("click", "8.1.8", "8.2.1")]
    held_back = [_update("numpy", "1.20", "2.4.6")]

    payload = json.loads(report.render("json", updated, held_back))

    assert payload == {
        "updated": [{"name": "click", "group": "project", "old": "8.1.8", "new": "8.2.1"}],
        "held_back": [{"name": "numpy", "group": "project", "old": "1.20", "new": "2.4.6"}],
    }


def test_render_markdown_lists_updates_and_held_back() -> None:
    updated = [_update("click", "8.1.8", "8.2.1")]
    held_back = [_update("numpy", "1.20", "2.4.6")]

    markdown = report.render("markdown", updated, held_back)

    assert "### Updated dependencies" in markdown
    assert "- ⬆️ `click` 8.1.8 → 8.2.1 (project)" in markdown
    assert "### Held back" in markdown
    assert "- `numpy` 1.20 → 2.4.6 (project)" in markdown


def test_render_markdown_empty() -> None:
    assert report.render("markdown", [], []) == "No dependencies were updated."


def test_render_json_empty() -> None:
    assert json.loads(report.render("json", [], [])) == {"updated": [], "held_back": []}
