"""
Module that reads project-level configuration from `[tool.uv-upsync]`.

Settings declared in `pyproject.toml` provide defaults so they do not have to be
repeated on every invocation. Command-line arguments always take precedence over
the configuration file, which in turn takes precedence over the built-in
defaults.
"""

from __future__ import annotations

import dataclasses

from typing import TYPE_CHECKING
from typing import Any

from uv_upsync import exceptions


if TYPE_CHECKING:
    import tomlkit


class ConfigError(exceptions.BaseError):
    """Raised when the `[tool.uv-upsync]` section is malformed."""


_BUMP_LEVELS = ("major", "minor", "patch")


@dataclasses.dataclass(frozen=True)
class Config:
    """Project-level defaults read from `[tool.uv-upsync]`."""

    exclude: tuple[str, ...] = ()
    group: tuple[str, ...] = ()
    upgrade_package: tuple[str, ...] = ()
    all_groups: bool = False
    prerelease: bool = False
    resolve: bool = False
    index_url: str | None = None
    max_bump: str | None = None


_LIST_FIELDS = {
    "exclude": "exclude",
    "group": "group",
    "upgrade-package": "upgrade_package",
}


def load_config(pyproject: tomlkit.TOMLDocument | dict[str, Any]) -> Config:
    """Read and validate the `[tool.uv-upsync]` section, if present."""
    raw = pyproject.get("tool", {}).get("uv-upsync", {})
    section = raw.unwrap() if hasattr(raw, "unwrap") else dict(raw)
    if not section:
        return Config()

    values: dict[str, Any] = {}
    for key, attribute in _LIST_FIELDS.items():
        if key in section:
            values[attribute] = _as_str_tuple(key, section[key])
    if "all-groups" in section:
        values["all_groups"] = _as_bool("all-groups", section["all-groups"])
    if "prerelease" in section:
        values["prerelease"] = _as_bool("prerelease", section["prerelease"])
    if "resolve" in section:
        values["resolve"] = _as_bool("resolve", section["resolve"])
    if "index-url" in section:
        values["index_url"] = _as_str("index-url", section["index-url"])
    if "max-bump" in section:
        values["max_bump"] = _as_choice("max-bump", section["max-bump"], _BUMP_LEVELS)

    return Config(**values)


def _as_choice(key: str, value: object, choices: tuple[str, ...]) -> str:
    if not isinstance(value, str) or value not in choices:
        allowed = ", ".join(choices)
        message = f"Invalid value for 'tool.uv-upsync.{key}': expected one of {allowed}"
        raise ConfigError(message)
    return value


def _as_str_tuple(key: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        message = f"Invalid value for 'tool.uv-upsync.{key}': expected a list of strings"
        raise ConfigError(message)
    return tuple(str(item) for item in value)


def _as_bool(key: str, value: object) -> bool:
    if not isinstance(value, bool):
        message = f"Invalid value for 'tool.uv-upsync.{key}': expected a boolean"
        raise ConfigError(message)
    return value


def _as_str(key: str, value: object) -> str:
    if not isinstance(value, str):
        message = f"Invalid value for 'tool.uv-upsync.{key}': expected a string"
        raise ConfigError(message)
    return value
