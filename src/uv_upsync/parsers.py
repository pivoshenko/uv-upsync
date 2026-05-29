"""Module that contains the TOML parsing and version-bumping logic.

Dependency specifiers are parsed with `packaging` (the canonical PEP 440/508
implementation) for correctness, while the actual rewrite is a surgical
replacement of the version token so that the author's formatting, operators,
extras and environment markers are preserved verbatim.
"""

from __future__ import annotations

import dataclasses

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from packaging.requirements import InvalidRequirement
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version
from tomlkit import items

from uv_upsync import logging


if TYPE_CHECKING:
    from collections.abc import Iterator
    from collections.abc import Sequence

    import tomlkit

    from packaging.specifiers import Specifier


logger = logging.Logger()

# Operators whose lower bound it is safe to raise. Pinned (`==`, `===`), upper
# bound (`<`, `<=`) and exclusion (`!=`) constraints are intentionally left
# untouched, mirroring uv's conservative `--upgrade` behavior.
UPGRADABLE_OPERATORS = frozenset({">=", ">", "~="})


@dataclasses.dataclass(frozen=True)
class Update:
    """A single version bump applied to a dependency specifier."""

    name: str
    old_version: str
    new_version: str


def iter_dependency_groups(
    pyproject: tomlkit.TOMLDocument,
    selected_groups: tuple[str, ...] = (),
    *,
    all_groups: bool = False,
) -> Iterator[tuple[str, items.Array]]:
    """Yield `(label, array)` for every selected dependency list in the document.

    The yielded arrays are the live tomlkit objects, so mutating them in place
    updates the underlying document while preserving formatting and comments.
    """
    project = cast("dict[str, Any]", pyproject.get("project", {}))

    dependencies = project.get("dependencies")
    if isinstance(dependencies, items.Array) and _is_selected(
        "project", selected_groups, all_groups=all_groups
    ):
        yield "project", dependencies

    optional = project.get("optional-dependencies", {})
    for name, array in optional.items():
        if isinstance(array, items.Array) and _is_selected(
            name, selected_groups, all_groups=all_groups
        ):
            yield f"optional-dependencies.{name}", array

    groups = pyproject.get("dependency-groups", {})
    for name, array in groups.items():
        if isinstance(array, items.Array) and _is_selected(
            name, selected_groups, all_groups=all_groups
        ):
            yield f"dependency-groups.{name}", array


def _is_selected(name: str, selected_groups: tuple[str, ...], *, all_groups: bool) -> bool:
    return all_groups or not selected_groups or name in selected_groups


def parse_requirement(specifier: str) -> Requirement | None:
    """Parse a specifier into a `Requirement`, returning `None` if it is not one."""
    try:
        return Requirement(specifier)
    except InvalidRequirement:
        return None


def upgradable_specifier(requirement: Requirement) -> Specifier | None:
    """Return the single specifier whose lower bound can be raised, else `None`."""
    specifiers = list(requirement.specifier)
    if len(specifiers) != 1:
        return None

    specifier = specifiers[0]
    if specifier.operator not in UPGRADABLE_OPERATORS:
        return None

    return specifier


def collect_package_names(
    dependency_specifiers: Sequence[object],
    exclude: tuple[str, ...],
    only: frozenset[str] = frozenset(),
) -> set[str]:
    """Collect the canonical names of packages that are candidates for an update."""
    names: set[str] = set()
    for specifier in dependency_specifiers:
        requirement = _candidate_requirement(specifier, exclude, only)
        if requirement is not None and upgradable_specifier(requirement) is not None:
            names.add(canonicalize_name(requirement.name))
    return names


def apply_updates(
    dependency_specifiers: items.Array,
    versions: dict[str, str | None],
    exclude: tuple[str, ...],
    only: frozenset[str] = frozenset(),
) -> list[Update]:
    """Rewrite the specifiers in place, returning the list of applied updates."""
    updates: list[Update] = []
    for index, specifier in enumerate(dependency_specifiers):
        requirement = _candidate_requirement(specifier, exclude, only)
        if requirement is None:
            continue

        target = upgradable_specifier(requirement)
        if target is None:
            continue

        text = cast("str", specifier)
        canonical_name = canonicalize_name(requirement.name)
        new_version = versions.get(canonical_name)
        old_version = target.version

        if new_version is None or Version(new_version) <= Version(old_version):
            logger.skip(f"Skipping {text} (up to date)")
            continue

        dependency_specifiers[index] = _replace_version(
            text,
            target.operator,
            old_version,
            new_version,
        )
        logger.update(requirement.name, old_version, new_version)
        updates.append(Update(requirement.name, old_version, new_version))

    return updates


def _candidate_requirement(
    specifier: object,
    exclude: tuple[str, ...],
    only: frozenset[str],
) -> Requirement | None:
    if isinstance(specifier, items.InlineTable) or not isinstance(specifier, str):
        return None

    requirement = parse_requirement(specifier)
    if requirement is None:
        logger.skip(f"Skipping {specifier!r} (not a valid specifier)")
        return None

    canonical_name = canonicalize_name(requirement.name)
    if requirement.name in exclude or canonical_name in {
        canonicalize_name(name) for name in exclude
    }:
        logger.skip(f"Skipping {specifier} (excluded)")
        return None

    if only and canonical_name not in only:
        return None

    return requirement


def _replace_version(specifier: str, operator: str, old_version: str, new_version: str) -> str:
    """Replace only the version token, preserving operators, spacing and markers."""
    requirement_part, separator, marker = specifier.partition(";")

    operator_index = requirement_part.find(operator)
    head = requirement_part[:operator_index]
    tail = requirement_part[operator_index:].replace(old_version, new_version, 1)

    return f"{head}{tail}{separator}{marker}"
