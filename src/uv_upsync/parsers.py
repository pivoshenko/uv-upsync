"""Module that contains the TOML parsing and version-bumping logic.

Dependency specifiers are parsed with `packaging` (the canonical PEP 440/508
implementation) for correctness, while the actual rewrite is a surgical
replacement of the version token so that the author's formatting, operators,
extras and environment markers are preserved verbatim.
"""

from __future__ import annotations

import re
import copy
import dataclasses

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from packaging.requirements import InvalidRequirement
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
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
PINNED_OPERATORS = frozenset({"==", "==="})
BUMP_LEVELS = ("major", "minor", "patch")


@dataclasses.dataclass(frozen=True)
class Update:
    """A planned version bump, locating the specifier and its replacement text."""

    group: str
    index: int
    name: str
    old_version: str
    new_version: str
    new_text: str
    text: str = ""
    operator: str = ""


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


def upgradable_specifier(requirement: Requirement) -> tuple[Specifier, SpecifierSet] | None:
    """Return the raisable lower-bound clause and the residual constraints, or `None`.

    Compound specifiers such as `>=1.0,<2.0` are supported: the single lower-bound
    clause is the one we raise, while the remaining clauses (caps, exclusions) are
    returned as a residual `SpecifierSet` that any new version must still satisfy.
    Pinned requirements (`==`, `===`) are never touched.
    """
    specifiers = list(requirement.specifier)
    if any(specifier.operator in PINNED_OPERATORS for specifier in specifiers):
        return None

    lower_indexes = [
        index
        for index, specifier in enumerate(specifiers)
        if specifier.operator in UPGRADABLE_OPERATORS
    ]
    if len(lower_indexes) != 1:
        return None

    lower_index = lower_indexes[0]
    residual = SpecifierSet(
        ",".join(
            str(specifier) for index, specifier in enumerate(specifiers) if index != lower_index
        ),
    )
    return specifiers[lower_index], residual


def select_new_version(
    versions: Sequence[Version],
    residual: SpecifierSet,
    old_version: str,
    *,
    allow_prerelease: bool = False,
    max_bump: str | None = None,
) -> str | None:
    """Pick the highest version greater than `old_version` allowed by the policies."""
    eligible = _eligible_versions(
        versions,
        residual,
        Version(old_version),
        allow_prerelease=allow_prerelease,
        max_bump=max_bump,
    )
    return str(eligible[-1]) if eligible else None


def eligible_versions(
    update: Update,
    versions: Sequence[Version],
    *,
    allow_prerelease: bool = False,
    max_bump: str | None = None,
) -> list[str]:
    """Return, ascending, every version `update` could be bumped to under the policies.

    Used by the resolver-aware search to look for a lower version that locks when the
    latest does not.
    """
    requirement = parse_requirement(update.text)
    if requirement is None:
        return []
    target = upgradable_specifier(requirement)
    if target is None:
        return []
    _, residual = target
    eligible = _eligible_versions(
        versions,
        residual,
        Version(update.old_version),
        allow_prerelease=allow_prerelease,
        max_bump=max_bump,
    )
    return [str(version) for version in eligible]


def at_version(update: Update, version: str) -> Update:
    """Return a copy of `update` rewritten to bump to `version` instead."""
    return dataclasses.replace(
        update,
        new_version=version,
        new_text=_replace_version(update.text, update.operator, update.old_version, version),
    )


def _eligible_versions(
    versions: Sequence[Version],
    residual: SpecifierSet,
    old: Version,
    *,
    allow_prerelease: bool,
    max_bump: str | None,
) -> list[Version]:
    return sorted(
        version
        for version in versions
        if version > old
        and (allow_prerelease or not (version.is_prerelease or version.is_devrelease))
        and residual.contains(version, prereleases=allow_prerelease)
        and _within_bump(old, version, max_bump)
    )


def find_conflicts(error_text: str, names: set[str], exclude: str) -> list[str]:
    """Find which other project dependencies are named in a uv resolver error."""
    haystack = error_text.lower()
    found: list[str] = []
    for name in sorted(names):
        if name == exclude:
            continue
        variants = {name, name.replace("-", "_")}
        if any(re.search(rf"\b{re.escape(variant)}\b", haystack) for variant in variants):
            found.append(name)
    return found


def collect_all_names(dependency_groups: Sequence[tuple[str, items.Array]]) -> set[str]:
    """Collect the canonical names of every declared dependency across the groups."""
    names: set[str] = set()
    for _, array in dependency_groups:
        for specifier in array:
            if not isinstance(specifier, str):
                continue
            requirement = parse_requirement(specifier)
            if requirement is not None:
                names.add(canonicalize_name(requirement.name))
    return names


def _within_bump(old: Version, new: Version, max_bump: str | None) -> bool:
    if max_bump is None or max_bump == "major":
        return True
    old_release = (*old.release, 0, 0)[:3]
    new_release = (*new.release, 0, 0)[:3]
    if max_bump == "minor":
        return new_release[0] == old_release[0]
    return new_release[:2] == old_release[:2]


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


def plan_updates(  # noqa: PLR0913
    dependency_groups: Sequence[tuple[str, items.Array]],
    versions: dict[str, list[Version]],
    exclude: tuple[str, ...],
    only: frozenset[str] = frozenset(),
    *,
    allow_prerelease: bool = False,
    max_bump: str | None = None,
) -> list[Update]:
    """Compute the version bumps for the given groups without mutating anything."""
    updates: list[Update] = []
    for label, array in dependency_groups:
        for index, specifier in enumerate(array):
            requirement = _candidate_requirement(specifier, exclude, only)
            if requirement is None:
                continue

            target = upgradable_specifier(requirement)
            if target is None:
                continue

            text = cast("str", specifier)
            lower, residual = target
            old_version = lower.version
            candidates = versions.get(canonicalize_name(requirement.name), [])
            new_version = select_new_version(
                candidates,
                residual,
                old_version,
                allow_prerelease=allow_prerelease,
                max_bump=max_bump,
            )

            if new_version is None:
                _log_skip(text, candidates, residual, old_version, max_bump=max_bump)
                continue

            updates.append(
                Update(
                    group=label,
                    index=index,
                    name=requirement.name,
                    old_version=old_version,
                    new_version=new_version,
                    new_text=_replace_version(text, lower.operator, old_version, new_version),
                    text=text,
                    operator=lower.operator,
                ),
            )

    return updates


def _log_skip(
    text: str,
    candidates: Sequence[Version],
    residual: SpecifierSet,
    old_version: str,
    *,
    max_bump: str | None,
) -> None:
    if max_bump is not None:
        held = select_new_version(candidates, residual, old_version, max_bump=None)
        if held is not None:
            logger.skip(f"Skipping {text} (v{held} exceeds --max-bump {max_bump})")
            return
    logger.skip(f"Skipping {text} (up to date)")


def apply_updates(
    pyproject: tomlkit.TOMLDocument,
    selected_groups: tuple[str, ...],
    updates: Sequence[Update],
    *,
    all_groups: bool = False,
) -> tomlkit.TOMLDocument:
    """Return a deep copy of the document with the given updates applied."""
    document = copy.deepcopy(pyproject)
    arrays = dict(iter_dependency_groups(document, selected_groups, all_groups=all_groups))
    for update in updates:
        arrays[update.group][update.index] = update.new_text
    return document


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
