"""Module that contains tests for the module that contains the TOML parsers."""

from __future__ import annotations

import typing

import pytest
import tomlkit

from packaging.version import Version
from tomlkit import items

from uv_upsync import parsers


def _versions(*raw: str) -> list[Version]:
    return [Version(value) for value in raw]


if typing.TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture(autouse=True)
def _silence_logger(mocker: MockerFixture) -> None:
    mocker.patch("uv_upsync.logging.Logger.skip")
    mocker.patch("uv_upsync.logging.Logger.update")


@pytest.mark.parametrize(
    ("selected", "all_groups", "expected_labels"),
    [
        ((), False, ["project", "optional-dependencies.dev", "dependency-groups.test"]),
        (("project",), False, ["project"]),
        (("dev",), False, ["optional-dependencies.dev"]),
        (("test",), False, ["dependency-groups.test"]),
        (("missing",), True, ["project", "optional-dependencies.dev", "dependency-groups.test"]),
    ],
)
def test_iter_dependency_groups(
    selected: tuple[str, ...],
    expected_labels: list[str],
    *,
    all_groups: bool,
) -> None:
    pyproject = tomlkit.parse(
        """
        [project]
        dependencies = ["click>=8.0.0"]
        [project.optional-dependencies]
        dev = ["pytest>=7.0.0"]
        [dependency-groups]
        test = ["coverage>=6.0.0"]
        """,
    )
    labels = [
        label
        for label, _ in parsers.iter_dependency_groups(pyproject, selected, all_groups=all_groups)
    ]
    assert labels == expected_labels


def test_iter_dependency_groups_handles_missing_sections() -> None:
    pyproject = tomlkit.parse("[project]\nname = 'demo'\n")
    assert list(parsers.iter_dependency_groups(pyproject)) == []


@pytest.mark.parametrize(
    ("specifier", "is_valid"),
    [
        ("click>=8.0.0", True),
        ("coverage[toml]>=7.0.0", True),
        ("click>=8.0.0; python_version >= '3.10'", True),
        ("invalid^1.0.0", False),
        ("pkg=1.0.0", False),
    ],
)
def test_parse_requirement(specifier: str, *, is_valid: bool) -> None:
    result = parsers.parse_requirement(specifier)
    assert (result is not None) is is_valid


@pytest.mark.parametrize(
    ("specifier", "is_upgradable"),
    [
        ("click>=8.0.0", True),
        ("httpx~=0.24.0", True),
        ("requests>2.0.0", True),
        ("pkg>=1.0.0,<2.0.0", True),  # compound range is now supported
        ("pkg>=1.0.0,!=1.5.0", True),
        ("pkg==1.0.0", False),
        ("pkg===1.0.0", False),
        ("pkg>=1.0.0,==1.2.0", False),  # pinned clause present
        ("pkg<=2.0.0", False),
        ("pkg<2.0.0", False),
        ("pkg!=2.0.0", False),
        ("pkg", False),  # no specifier
    ],
)
def test_upgradable_specifier(specifier: str, *, is_upgradable: bool) -> None:
    requirement = parsers.parse_requirement(specifier)
    assert requirement is not None
    assert (parsers.upgradable_specifier(requirement) is not None) is is_upgradable


def test_upgradable_specifier_returns_lower_and_residual() -> None:
    requirement = parsers.parse_requirement("pkg>=1.0.0,<2.0.0")
    assert requirement is not None
    result = parsers.upgradable_specifier(requirement)
    assert result is not None
    lower, residual = result
    assert lower.operator == ">="
    assert lower.version == "1.0.0"
    assert str(residual) == "<2.0.0"


def test_collect_package_names() -> None:
    specifiers = ["click>=8.0.0", "Coverage[toml]>=7.0.0", "pinned==1.0.0", "pytest"]
    names = parsers.collect_package_names(specifiers, ())
    assert names == {"click", "coverage"}


def test_collect_package_names_respects_exclude_and_only() -> None:
    specifiers = ["click>=8.0.0", "httpx>=0.24.0", "ruff>=0.1.0"]
    assert parsers.collect_package_names(specifiers, ("click",)) == {"httpx", "ruff"}
    assert parsers.collect_package_names(specifiers, (), frozenset({"httpx"})) == {"httpx"}


def _array(specifiers: list[str]) -> items.Array:
    array = tomlkit.array()
    array.extend(specifiers)
    return array


def _groups(specifiers: list[str]) -> list[tuple[str, items.Array]]:
    return [("project", _array(specifiers))]


@pytest.mark.parametrize(
    ("specifier", "name", "latest", "expected"),
    [
        ("click>=8.0.0", "click", "8.1.7", "click>=8.1.7"),
        ("httpx~=0.24.0", "httpx", "0.28.1", "httpx~=0.28.1"),
        ("requests>2.0.0", "requests", "2.31.0", "requests>2.31.0"),
        (
            "click>=8.0.0; python_version>='3.8'",
            "click",
            "8.1.7",
            "click>=8.1.7; python_version>='3.8'",
        ),
    ],
)
def test_plan_updates_computes_bump(
    specifier: str,
    name: str,
    latest: str,
    expected: str,
) -> None:
    updates = parsers.plan_updates(_groups([specifier]), {name: _versions(latest)}, ())
    assert len(updates) == 1
    assert updates[0].new_text == expected
    assert updates[0].group == "project"
    assert updates[0].index == 0


def test_plan_updates_raises_floor_within_compound_range() -> None:
    # the cap is respected: 2.0.0 is available but excluded by <2.0.0
    versions = {"pkg": _versions("1.0.0", "1.9.0", "2.0.0")}
    updates = parsers.plan_updates(_groups(["pkg>=1.0.0,<2.0.0"]), versions, ())
    assert len(updates) == 1
    assert updates[0].new_text == "pkg>=1.9.0,<2.0.0"


def test_plan_updates_skips_when_up_to_date() -> None:
    assert parsers.plan_updates(_groups(["click>=8.1.7"]), {"click": _versions("8.1.7")}, ()) == []


def test_plan_updates_skips_when_no_version_found() -> None:
    assert parsers.plan_updates(_groups(["click>=8.0.0"]), {"click": []}, ()) == []


def test_plan_updates_skips_pinned_and_invalid() -> None:
    assert parsers.plan_updates(_groups(["pinned==1.0.0", "invalid^1.0.0"]), {}, ()) == []


def test_plan_updates_ignores_inline_tables() -> None:
    inline_table = tomlkit.inline_table()
    inline_table["include-group"] = "extra"
    array = _array([])
    array.append(inline_table)

    assert parsers.plan_updates([("project", array)], {}, ()) == []


def test_plan_updates_respects_exclude() -> None:
    versions = {"click": _versions("9.0.0")}
    assert parsers.plan_updates(_groups(["click>=8.0.0"]), versions, ("click",)) == []


def test_plan_updates_skips_prereleases_by_default() -> None:
    versions = {"pkg": _versions("1.0.0", "2.0.0b1")}
    assert parsers.plan_updates(_groups(["pkg>=1.0.0"]), versions, ()) == []


def test_plan_updates_allows_prereleases_when_enabled() -> None:
    versions = {"pkg": _versions("1.0.0", "2.0.0b1")}
    updates = parsers.plan_updates(_groups(["pkg>=1.0.0"]), versions, (), allow_prerelease=True)
    assert updates[0].new_text == "pkg>=2.0.0b1"


def test_plan_updates_respects_max_bump() -> None:
    versions = {"pkg": _versions("1.0.0", "1.4.0", "2.0.0")}
    updates = parsers.plan_updates(_groups(["pkg>=1.0.0"]), versions, (), max_bump="minor")
    assert updates[0].new_text == "pkg>=1.4.0"


def test_plan_updates_reports_bump_held_back_by_max_bump(mocker: MockerFixture) -> None:
    skip = mocker.patch("uv_upsync.logging.Logger.skip")
    versions = {"pkg": _versions("1.0.0", "2.0.0")}  # only a major bump is available

    updates = parsers.plan_updates(_groups(["pkg>=1.0.0"]), versions, (), max_bump="minor")

    assert updates == []
    assert any("exceeds --max-bump" in call.args[0] for call in skip.call_args_list)


def test_apply_updates_builds_document_without_mutating_original() -> None:
    pyproject = tomlkit.parse('[project]\ndependencies = ["click>=8.0.0", "httpx>=0.24.0"]\n')
    groups = list(parsers.iter_dependency_groups(pyproject))
    versions = {"click": _versions("8.4.1"), "httpx": _versions("0.28.1")}
    updates = parsers.plan_updates(groups, versions, ())

    only_click = [update for update in updates if update.name == "click"]
    document = parsers.apply_updates(pyproject, (), only_click)

    assert document.unwrap()["project"]["dependencies"] == ["click>=8.4.1", "httpx>=0.24.0"]
    # the original document is left untouched
    assert pyproject.unwrap()["project"]["dependencies"] == ["click>=8.0.0", "httpx>=0.24.0"]


def test_apply_updates_applies_subset_across_groups() -> None:
    pyproject = tomlkit.parse(
        """
        [project]
        dependencies = ["click>=8.0.0"]
        [dependency-groups]
        test = ["pytest>=7.0.0"]
        """,
    )
    groups = list(parsers.iter_dependency_groups(pyproject))
    versions = {"click": _versions("8.4.1"), "pytest": _versions("9.0.0")}
    updates = parsers.plan_updates(groups, versions, ())

    document = parsers.apply_updates(pyproject, (), updates).unwrap()
    assert document["project"]["dependencies"] == ["click>=8.4.1"]
    assert document["dependency-groups"]["test"] == ["pytest>=9.0.0"]


@pytest.mark.parametrize(
    ("residual", "max_bump", "allow_prerelease", "expected"),
    [
        ("", None, False, "2.0.0"),
        ("<2.0.0", None, False, "1.9.0"),
        ("", "minor", False, "1.9.0"),
        ("", "patch", False, "1.0.5"),
        ("", None, True, "2.1.0rc1"),
    ],
)
def test_select_new_version(
    residual: str,
    max_bump: str | None,
    expected: str,
    *,
    allow_prerelease: bool,
) -> None:
    versions = _versions("1.0.0", "1.0.5", "1.9.0", "2.0.0", "2.1.0rc1")
    result = parsers.select_new_version(
        versions,
        parsers.SpecifierSet(residual),
        "1.0.0",
        allow_prerelease=allow_prerelease,
        max_bump=max_bump,
    )
    assert result == expected


def test_select_new_version_returns_none_when_nothing_newer() -> None:
    assert parsers.select_new_version(_versions("1.0.0"), parsers.SpecifierSet(), "1.0.0") is None


@pytest.mark.parametrize(
    ("specifier", "operator", "old", "new", "expected"),
    [
        (
            "tomlkit >= 0.10.0 ; python_version >= '3.10'",
            ">=",
            "0.10.0",
            "0.15.0",
            "tomlkit >= 0.15.0 ; python_version >= '3.10'",
        ),
        ("click >=  8.0.0", ">=", "8.0.0", "8.4.1", "click >=  8.4.1"),
        ("httpx~=0.24.0", "~=", "0.24.0", "0.28.1", "httpx~=0.28.1"),
    ],
)
def test_replace_version_preserves_formatting(
    specifier: str,
    operator: str,
    old: str,
    new: str,
    expected: str,
) -> None:
    assert parsers._replace_version(specifier, operator, old, new) == expected
