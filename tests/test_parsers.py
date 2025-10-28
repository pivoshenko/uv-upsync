"""Module that contains tests for the module that contains implementation of the TOML parsers."""

from __future__ import annotations

import typing

import pytest
import tomlkit

from uv_upsync import exceptions
from uv_upsync import parsers


if typing.TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.mark.parametrize(
    ("pyproject_content", "expected_groups"),
    [
        (
            """
            [project]
            dependencies = ["click>=8.0.0", "httpx>=0.24.0"]
            """,
            {"project": ["click>=8.0.0", "httpx>=0.24.0"]},
        ),
        (
            """
            [project]
            dependencies = []
            """,
            {},
        ),
        (
            """
            [project]
            dependencies = ["click>=8.0.0"]
            [project.optional-dependencies]
            dev = ["pytest>=7.0.0"]
            """,
            {
                "project": ["click>=8.0.0"],
                "optional-dependencies": {"dev": ["pytest>=7.0.0"]},
            },
        ),
        (
            """
            [project]
            dependencies = ["click>=8.0.0"]
            [dependency-groups]
            test = ["pytest>=7.0.0"]
            """,
            {
                "project": ["click>=8.0.0"],
                "dependency-groups": {"test": ["pytest>=7.0.0"]},
            },
        ),
        (
            """
            [project]
            """,
            {},
        ),
    ],
)
def test_get_dependencies_groups(
    pyproject_content: str,
    expected_groups: dict[str, list[str] | dict[str, list[str]]],
) -> None:
    pyproject = tomlkit.parse(pyproject_content)
    groups = parsers.get_dependencies_groups(pyproject)
    assert groups == expected_groups


@pytest.mark.parametrize(
    ("dependency_specifier", "expected_name", "expected_operator"),
    [
        ("click>=8.0.0", "click", ">="),
        ("httpx==0.24.0", "httpx", "=="),
        ("pytest~=7.0.0", "pytest", "~="),
        ("requests>2.0.0", "requests", ">"),
        ("flask<=2.0.0", "flask", "<="),
        ("django<4.0.0", "django", "<"),
        ("package===1.0.0", "package", "==="),
        ("package-name>=1.0.0", "package-name", ">="),
        ("package_name>=1.0.0", "package_name", ">="),
        ("package >=  1.0.0", "package", ">="),
    ],
)
def test_get_dependency_name_and_operator_valid(
    dependency_specifier: str,
    expected_name: str,
    expected_operator: str,
) -> None:
    name, operator = parsers.get_dependency_name_and_operator(dependency_specifier)
    assert name == expected_name
    assert operator == expected_operator


@pytest.mark.parametrize(
    ("dependency_specifier", "expected_exception"),
    [
        ("package^1.0.0", exceptions.InvalidDependencySpecifierError),
        ("package/1.0.0", exceptions.InvalidDependencySpecifierError),
        ("package:1.0.0", exceptions.InvalidDependencySpecifierError),
        ("package@1.0.0", exceptions.InvalidDependencySpecifierError),
        ("package", exceptions.NoOperatorFoundError),
        ("package-name", exceptions.NoOperatorFoundError),
        ("package>=1.0.0,<2.0.0", exceptions.MultipleOperatorsFoundError),
        ("package>=1.0.0,<=2.0.0", exceptions.MultipleOperatorsFoundError),
    ],
)
def test_get_dependency_name_and_operator_invalid(
    dependency_specifier: str,
    expected_exception: type[exceptions.BaseError],
) -> None:
    with pytest.raises(expected_exception):
        parsers.get_dependency_name_and_operator(dependency_specifier)


@pytest.mark.parametrize(
    ("dependency_specifier", "operator", "exclude", "should_update"),
    [
        ("click>=8.0.0", ">=", (), True),
        ("click==8.0.0", "==", (), False),  # == Operator ignored
        ("click<=8.0.0", "<=", (), False),  # <= Operator ignored
        ("click<8.0.0", "<", (), False),  # < Operator ignored
        ("click>=8.0.0", ">=", ("click",), False),  # Excluded by name
        ("httpx~=0.24.0", "~=", (), True),
        ("requests>2.0.0", ">", (), True),
    ],
)
def test_update_dependency_specifier(
    mocker: MockerFixture,
    dependency_specifier: str,
    operator: str,
    exclude: tuple[str, ...],
    *,
    should_update: bool,
) -> None:
    mock_fetch = mocker.patch(
        "uv_upsync.pypi.fetch_latest_dependency_version",
        return_value="9.9.9",
    )
    mocker.patch("uv_upsync.logging.Logger.warning")
    mocker.patch("uv_upsync.logging.Logger.info")

    specifier = parsers.update_dependency_specifier(dependency_specifier, exclude)

    if should_update:
        assert mock_fetch.called
        assert "9.9.9" in specifier
    elif exclude or operator in ("==", "<=", "<"):
        assert specifier == dependency_specifier


@pytest.mark.parametrize(
    ("dependency_specifier", "latest_version", "expected_specifier"),
    [
        ("click>=8.0.0", "8.1.7", "click>=8.1.7"),
        ("httpx~=0.24.0", "0.28.1", "httpx~=0.28.1"),
        ("requests>2.0.0", "2.31.0", "requests>2.31.0"),
        ("click>=8.0.0;python_version>='3.8'", "8.1.7", "click>=8.1.7;python_version>='3.8'"),
        ("click>=8.0.0; python_version>='3.8'", "8.1.7", "click>=8.1.7; python_version>='3.8'"),
    ],
)
def test_update_dependency_specifier_with_version(
    mocker: MockerFixture,
    dependency_specifier: str,
    latest_version: str,
    expected_specifier: str,
) -> None:
    mocker.patch(
        "uv_upsync.pypi.fetch_latest_dependency_version",
        return_value=latest_version,
    )
    mocker.patch("uv_upsync.logging.Logger.warning")
    mocker.patch("uv_upsync.logging.Logger.info")

    specifier = parsers.update_dependency_specifier(dependency_specifier, ())
    assert specifier == expected_specifier


def test_update_dependency_specifier_fetch_returns_none(mocker: MockerFixture) -> None:
    mocker.patch("uv_upsync.pypi.fetch_latest_dependency_version", return_value=None)
    mocker.patch("uv_upsync.logging.Logger.warning")
    mocker.patch("uv_upsync.logging.Logger.info")

    dependency_specifier = "click>=8.0.0"
    specifier = parsers.update_dependency_specifier(dependency_specifier, ())
    assert specifier == dependency_specifier


@pytest.mark.parametrize(
    ("dependency_specifiers", "exclude", "expected_count"),
    [
        (["click>=8.0.0", "httpx>=0.24.0"], (), 2),
        (["click>=8.0.0", "httpx>=0.24.0"], ("click",), 2),
        (["click>=8.0.0"], (), 1),
        ([], (), 0),
    ],
)
def test_update_dependency_specifiers(
    mocker: MockerFixture,
    dependency_specifiers: list[str],
    exclude: tuple[str, ...],
    expected_count: int,
) -> None:
    mocker.patch("uv_upsync.pypi.fetch_latest_dependency_version", return_value="9.9.9")
    mocker.patch("uv_upsync.logging.Logger.warning")
    mocker.patch("uv_upsync.logging.Logger.info")

    specifiers = parsers.update_dependency_specifiers(dependency_specifiers, exclude)
    assert len(specifiers) == expected_count


def test_update_dependency_specifiers_with_inline_table(mocker: MockerFixture) -> None:
    mocker.patch("uv_upsync.logging.Logger.warning")
    mocker.patch("uv_upsync.logging.Logger.info")

    inline_table = tomlkit.inline_table()
    inline_table["git"] = "https://github.com/user/repo.git"

    dependency_specifiers = [inline_table]  # type: ignore[list-item]
    specifiers = parsers.update_dependency_specifiers(dependency_specifiers, ())

    assert len(specifiers) == 1
    assert specifiers[0] == inline_table


def test_update_dependency_specifiers_with_invalid_specifier(mocker: MockerFixture) -> None:
    mocker.patch("uv_upsync.logging.Logger.warning")
    mocker.patch("uv_upsync.logging.Logger.info")
    mocker.patch("uv_upsync.logging.Logger.exception")

    dependency_specifiers = ["invalid^1.0.0"]
    specifiers = parsers.update_dependency_specifiers(dependency_specifiers, ())

    assert len(specifiers) == 1
    assert specifiers[0] == "invalid^1.0.0"


@pytest.mark.parametrize(
    ("dependency_specifiers", "exclude"),
    [
        (["click>=8.0.0", "httpx>=0.24.0", "pytest>=7.0.0"], ("pytest",)),
        (["package1>=1.0.0", "package2>=2.0.0"], ("package1", "package2")),
    ],
)
def test_update_dependency_specifiers_with_exclusions(
    mocker: MockerFixture,
    dependency_specifiers: list[str],
    exclude: tuple[str, ...],
) -> None:
    mocker.patch(
        "uv_upsync.pypi.fetch_latest_dependency_version",
        return_value="9.9.9",
    )
    mocker.patch("uv_upsync.logging.Logger.warning")
    mocker.patch("uv_upsync.logging.Logger.info")

    specifiers = parsers.update_dependency_specifiers(dependency_specifiers, exclude)

    assert len(specifiers) == len(dependency_specifiers)

    for dependency in dependency_specifiers:
        if any(exc in dependency for exc in exclude):
            assert dependency in specifiers
