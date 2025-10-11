"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_logger_singleton() -> None:
    from uv_plugin_up.logging import SingletonMeta  # noqa: PLC0415

    SingletonMeta._instances.clear()  # noqa: SLF001
