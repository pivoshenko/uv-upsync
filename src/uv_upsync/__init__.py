"""uv-upsync - is a tool for automated dependency updates and version bumping in pyproject.toml."""

from __future__ import annotations

from importlib.metadata import version


__version__ = version("uv-upsync")
