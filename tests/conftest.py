"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_logger_singleton() -> None:
    from uv_upsync.logging import Logger  # noqa: PLC0415

    Logger._instance = None  # noqa: SLF001
