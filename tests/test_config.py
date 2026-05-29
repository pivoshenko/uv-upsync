"""Module that contains tests for the [tool.uv-upsync] configuration reader."""

from __future__ import annotations

import pytest
import tomlkit

from uv_upsync import config


def test_load_config_returns_defaults_when_absent() -> None:
    assert config.load_config(tomlkit.parse("[project]\nname = 'demo'\n")) == config.Config()


def test_load_config_reads_all_fields() -> None:
    pyproject = tomlkit.parse(
        """
        [tool.uv-upsync]
        exclude = ["click", "ruff"]
        group = ["test"]
        upgrade-package = ["httpx"]
        all-groups = true
        prerelease = true
        resolve = true
        index-url = "https://example.com/simple"
        max-bump = "minor"
        """,
    )
    settings = config.load_config(pyproject)

    assert settings.exclude == ("click", "ruff")
    assert settings.group == ("test",)
    assert settings.upgrade_package == ("httpx",)
    assert settings.all_groups is True
    assert settings.prerelease is True
    assert settings.resolve is True
    assert settings.index_url == "https://example.com/simple"
    assert settings.max_bump == "minor"


def test_load_config_reads_plain_dict() -> None:
    settings = config.load_config({"tool": {"uv-upsync": {"exclude": ["click"]}}})
    assert settings.exclude == ("click",)
    assert settings.all_groups is False


@pytest.mark.parametrize(
    "section",
    [
        "exclude = 'click'",  # not a list
        "exclude = [1, 2]",  # not strings
        "group = 42",
        "upgrade-package = true",
    ],
)
def test_load_config_rejects_invalid_lists(section: str) -> None:
    pyproject = tomlkit.parse(f"[tool.uv-upsync]\n{section}\n")
    with pytest.raises(config.ConfigError):
        config.load_config(pyproject)


def test_load_config_rejects_invalid_bool() -> None:
    pyproject = tomlkit.parse("[tool.uv-upsync]\nall-groups = 'yes'\n")
    with pytest.raises(config.ConfigError):
        config.load_config(pyproject)


def test_load_config_rejects_invalid_index_url() -> None:
    pyproject = tomlkit.parse("[tool.uv-upsync]\nindex-url = 42\n")
    with pytest.raises(config.ConfigError):
        config.load_config(pyproject)


@pytest.mark.parametrize("value", ["'huge'", "42"])
def test_load_config_rejects_invalid_max_bump(value: str) -> None:
    pyproject = tomlkit.parse(f"[tool.uv-upsync]\nmax-bump = {value}\n")
    with pytest.raises(config.ConfigError):
        config.load_config(pyproject)
