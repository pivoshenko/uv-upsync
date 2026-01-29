"""Module that contains implementation of the TOML parsers."""

from __future__ import annotations

import re

from typing import TYPE_CHECKING

import tomlkit

from tomlkit import items

from uv_upsync import exceptions
from uv_upsync import logging
from uv_upsync import pypi


if TYPE_CHECKING:
    from collections.abc import Sequence


logger = logging.Logger()


def get_dependencies_groups(pyproject: tomlkit.TOMLDocument) -> dict[str, list]:
    dependencies_groups = {}

    project_dependencies = list(pyproject["project"].get("dependencies", []))  # type: ignore[union-attr]
    match project_dependencies:
        case []:
            pass
        case _:
            dependencies_groups.update({"project": project_dependencies})

    optional_dependencies = dict(pyproject["project"].get("optional-dependencies", {}))  # type: ignore[union-attr]
    match optional_dependencies:
        case _ if optional_dependencies:
            dependencies_groups.update({"optional-dependencies": optional_dependencies})

    dependency_groups = dict(pyproject.get("dependency-groups", {}))
    match dependency_groups:
        case _ if dependency_groups:
            dependencies_groups.update({"dependency-groups": dependency_groups})

    return dependencies_groups


def get_dependency_name_and_operator(dependency_specifier: str) -> tuple[str, str]:
    valid_operators = ("===", "==", "~=", ">=", ">", "<=", "<")
    invalid_operators = ("^", "/", ":", "@")

    # Strip environment markers (everything after semicolon) before parsing
    dependency_part = dependency_specifier.split(";")[0]

    match any(operator in dependency_part for operator in invalid_operators):
        case True:
            raise exceptions.InvalidDependencySpecifierError(dependency_specifier)
        case False:
            pass

    operators = re.findall("|".join(valid_operators), dependency_part)
    match len(operators):
        case 0:
            raise exceptions.NoOperatorFoundError(dependency_specifier)
        case 1:
            operator, *_ = operators
            dependency_name, *_ = dependency_part.replace(" ", "").split(operator)
            return dependency_name.strip(), operator.strip()
        case _:
            raise exceptions.MultipleOperatorsFoundError(dependency_specifier)


def update_dependency_specifier(dependency_specifier: str, exclude: tuple[str, ...]) -> str:
    ignore_operators = ("==", "<=", "<")

    dependency_name, operator = get_dependency_name_and_operator(dependency_specifier)
    match dependency_name in exclude:
        case True:
            logger.warning(f"Excluding dependency {dependency_name!r}")
            return dependency_specifier
        case False:
            pass

    match operator in ignore_operators:
        case True:
            logger.warning(f"Excluding dependency {dependency_name!r}")
            return dependency_specifier
        case False:
            pass

    latest_dependency_version = pypi.fetch_latest_dependency_version(dependency_name)
    match latest_dependency_version:
        case None:
            return dependency_specifier
        case _:
            match ";" in dependency_specifier:
                case True:
                    after_semi = "".join(dependency_specifier.split(";")[1:])
                    updated_dependency_specifier = (
                        f"{dependency_name}{operator}{latest_dependency_version};{after_semi}"
                    )
                case False:
                    updated_dependency_specifier = (
                        f"{dependency_name}{operator}{latest_dependency_version}"
                    )

    return updated_dependency_specifier


def update_dependency_specifiers(
    dependency_specifiers: Sequence[object],
    exclude: tuple[str, ...],
) -> list[object]:
    updated_dependency_specifiers = []
    for dependency_specifier in dependency_specifiers:
        # Inline tables (tomlkit inline_table) are not string specifiers
        if isinstance(dependency_specifier, items.InlineTable):
            logger.warning(f"Skipping inline table: {dependency_specifier!r}")
            updated_dependency_specifiers.append(dependency_specifier)
            continue

        # Only strings are processed for version lookups and exclusions
        if isinstance(dependency_specifier, str):
            if any(d_exclude in dependency_specifier for d_exclude in exclude):
                logger.warning(f"Skipping {dependency_specifier!r} (excluded)")
                updated_dependency_specifiers.append(dependency_specifier)
                continue

            try:
                get_dependency_name_and_operator(dependency_specifier)
            except exceptions.BaseError as exception:
                logger.exception(f"Skipping invalid specifier: {dependency_specifier!r}", exception)
                updated_dependency_specifiers.append(dependency_specifier)
                continue

            updated_dependency_specifier = update_dependency_specifier(
                dependency_specifier, exclude
            )
            if dependency_specifier != updated_dependency_specifier:
                logger.info(
                    f"Updating {dependency_specifier!r} to {updated_dependency_specifier!r}"
                )
                updated_dependency_specifiers.append(updated_dependency_specifier)
            else:
                logger.warning(f"Skipping {dependency_specifier!r} (no new version available)")
                updated_dependency_specifiers.append(dependency_specifier)
            continue

        # Unknown types: append as-is
        updated_dependency_specifiers.append(dependency_specifier)

    return updated_dependency_specifiers
