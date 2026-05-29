"""Module that contains tests for the module that contains the TOML parsers."""

from __future__ import annotations

import typing

import pytest
import tomlkit

from tomlkit import items

from uv_upsync import parsers


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
        ("pkg==1.0.0", False),
        ("pkg===1.0.0", False),
        ("pkg<=2.0.0", False),
        ("pkg<2.0.0", False),
        ("pkg!=2.0.0", False),
        ("pkg>=1.0.0,<2.0.0", False),  # multiple specifiers
        ("pkg", False),  # no specifier
    ],
)
def test_upgradable_specifier(specifier: str, *, is_upgradable: bool) -> None:
    requirement = parsers.parse_requirement(specifier)
    assert requirement is not None
    assert (parsers.upgradable_specifier(requirement) is not None) is is_upgradable


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
    updates = parsers.plan_updates(_groups([specifier]), {name: latest}, ())
    assert len(updates) == 1
    assert updates[0].new_text == expected
    assert updates[0].group == "project"
    assert updates[0].index == 0


def test_plan_updates_skips_when_up_to_date() -> None:
    assert parsers.plan_updates(_groups(["click>=8.1.7"]), {"click": "8.1.7"}, ()) == []


def test_plan_updates_skips_when_no_version_found() -> None:
    assert parsers.plan_updates(_groups(["click>=8.0.0"]), {"click": None}, ()) == []


def test_plan_updates_skips_pinned_and_invalid() -> None:
    assert parsers.plan_updates(_groups(["pinned==1.0.0", "invalid^1.0.0"]), {}, ()) == []


def test_plan_updates_ignores_inline_tables() -> None:
    inline_table = tomlkit.inline_table()
    inline_table["include-group"] = "extra"
    array = _array([])
    array.append(inline_table)

    assert parsers.plan_updates([("project", array)], {}, ()) == []


def test_plan_updates_respects_exclude() -> None:
    assert parsers.plan_updates(_groups(["click>=8.0.0"]), {"click": "9.0.0"}, ("click",)) == []


def test_apply_updates_builds_document_without_mutating_original() -> None:
    pyproject = tomlkit.parse('[project]\ndependencies = ["click>=8.0.0", "httpx>=0.24.0"]\n')
    groups = list(parsers.iter_dependency_groups(pyproject))
    updates = parsers.plan_updates(groups, {"click": "8.4.1", "httpx": "0.28.1"}, ())

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
    updates = parsers.plan_updates(groups, {"click": "8.4.1", "pytest": "9.0.0"}, ())

    document = parsers.apply_updates(pyproject, (), updates).unwrap()
    assert document["project"]["dependencies"] == ["click>=8.4.1"]
    assert document["dependency-groups"]["test"] == ["pytest>=9.0.0"]


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
