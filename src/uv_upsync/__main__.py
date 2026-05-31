"""Module that contains the main entry point for uv-upsync."""

from __future__ import annotations

import os
import copy
import time
import pathlib

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

import click
import tomlkit

from packaging.utils import canonicalize_name
from tomlkit.exceptions import TOMLKitError

from uv_upsync import __version__
from uv_upsync import commands
from uv_upsync import config as upsync_config
from uv_upsync import exceptions
from uv_upsync import logging
from uv_upsync import parsers
from uv_upsync import pypi
from uv_upsync import report
from uv_upsync import uv


if TYPE_CHECKING:
    from packaging.version import Version
    from tomlkit import items


logger = logging.Logger()

COLOR_CHOICES = {"auto": None, "always": True, "never": False}
ERROR_EXIT_CODE = 2


def _resolve_filepath(
    filepath: pathlib.Path | None,
    project: pathlib.Path | None,
) -> pathlib.Path:
    if filepath is not None:
        return filepath
    if project is not None:
        return project / "pyproject.toml"
    return pathlib.Path.cwd() / "pyproject.toml"


@click.command(cls=commands.Command)
@click.version_option(__version__, "-V", "--version", message="%(prog)s %(version)s")
@click.option(
    "--project",
    type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path),
    default=None,
    help="Path to the project directory containing the pyproject.toml file",
)
@click.option(
    "--directory",
    type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path),
    default=None,
    help="Change to DIR before running",
)
@click.option(
    "-f",
    "--filepath",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    default=None,
    hidden=True,
    help="Path to the pyproject.toml file (deprecated, use --project)",
)
@click.option(
    "-P",
    "--upgrade-package",
    "upgrade_package",
    type=click.STRING,
    multiple=True,
    default=(),
    help="Allow upgrades for only the given package(s)",
)
@click.option(
    "--exclude",
    type=click.STRING,
    multiple=True,
    default=(),
    help="Package(s) to exclude from upgrading",
)
@click.option(
    "--group",
    type=click.STRING,
    multiple=True,
    default=(),
    help="Upgrade dependencies in the given group(s) only",
)
@click.option(
    "--all-groups",
    is_flag=True,
    default=False,
    help="Upgrade dependencies in all groups",
)
@click.option(
    "--index-url",
    type=click.STRING,
    default=None,
    help="Base URL of the PEP 691 package index (defaults to the project's uv index or PyPI)",
)
@click.option(
    "--offline",
    is_flag=True,
    default=False,
    help="Disable network access, using only cached data",
)
@click.option(
    "-n",
    "--no-cache",
    is_flag=True,
    default=False,
    help="Avoid reading from or writing to the cache",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview the upgrades without writing to pyproject.toml",
)
@click.option(
    "--check",
    is_flag=True,
    default=False,
    help="Exit with a non-zero status if any upgrades are available",
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Roll back every upgrade and fail if the result does not lock",
)
@click.option(
    "--no-lock",
    "no_lock",
    is_flag=True,
    default=False,
    help="Write the upgrades without running uv lock",
)
@click.option(
    "--resolve",
    is_flag=True,
    default=False,
    help="When an upgrade does not lock, search for the latest version that does",
)
@click.option(
    "--max-bump",
    "max_bump",
    type=click.Choice(["major", "minor", "patch"]),
    default=None,
    help="Limit upgrades to at most this release level (holds back larger bumps)",
)
@click.option(
    "--prerelease",
    is_flag=True,
    default=False,
    help="Allow upgrading to pre-release versions",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
    help="Output format for the summary of upgrades",
)
@click.option("-q", "--quiet", is_flag=True, default=False, help="Use quiet output")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Use verbose output")
@click.option(
    "--color",
    type=click.Choice(["auto", "always", "never"]),
    default="auto",
    help="Control the use of color in output",
)
def cli(  # noqa: C901, PLR0913, PLR0915
    project: pathlib.Path | None,
    directory: pathlib.Path | None,
    filepath: pathlib.Path | None,
    upgrade_package: tuple[str, ...],
    exclude: tuple[str, ...],
    group: tuple[str, ...],
    index_url: str | None,
    max_bump: str | None,
    output_format: str,
    *,
    all_groups: bool,
    offline: bool,
    no_cache: bool,
    dry_run: bool,
    check: bool,
    strict: bool,
    no_lock: bool,
    resolve: bool,
    prerelease: bool,
    quiet: bool,
    verbose: bool,
    color: str,
) -> None:
    """Automated dependency upgrades and version bumping for pyproject.toml."""
    use_color = COLOR_CHOICES[color]
    if use_color is None and os.environ.get("NO_COLOR"):
        use_color = False
    # Machine-readable formats keep stdout clean by suppressing the status lines.
    logger.configure(quiet=quiet or output_format != "text", verbose=verbose, color=use_color)

    if directory is not None:
        os.chdir(directory)

    filepath = _resolve_filepath(filepath, project)
    if not filepath.is_file():
        logger.error(f"No pyproject.toml found at {filepath}")
        raise click.exceptions.Exit(ERROR_EXIT_CODE)

    try:
        with filepath.open() as toml_file:
            pyproject = tomlkit.load(toml_file)
    except (OSError, TOMLKitError) as exception:
        logger.exception(f"Failed to read {filepath}", cause=exception)
        raise click.exceptions.Exit(ERROR_EXIT_CODE) from exception
    backup = copy.deepcopy(pyproject)

    # Resolve settings with the precedence: CLI > [tool.uv-upsync] > defaults.
    settings = upsync_config.load_config(pyproject)
    exclude = exclude or settings.exclude
    group = group or settings.group
    upgrade_package = upgrade_package or settings.upgrade_package
    all_groups = all_groups or settings.all_groups
    index_url = index_url or settings.index_url
    max_bump = max_bump or settings.max_bump
    prerelease = prerelease or settings.prerelease
    resolve = resolve or settings.resolve

    only = frozenset(canonicalize_name(name) for name in upgrade_package)
    dependency_groups = list(
        parsers.iter_dependency_groups(pyproject, group, all_groups=all_groups)
    )

    resolved_index_url = index_url or pypi.index_url_from_pyproject(
        cast("dict[str, Any]", pyproject),
    )

    package_names: set[str] = set()
    for _, array in dependency_groups:
        package_names |= parsers.collect_package_names(array, exclude, only)

    started_at = time.perf_counter()
    with pypi.PyPIClient(
        resolved_index_url or pypi.DEFAULT_INDEX_URL,
        offline=offline,
        no_cache=no_cache,
    ) as client:
        versions = client.fetch_many(package_names)
    elapsed_ms = (time.perf_counter() - started_at) * 1000

    updates = parsers.plan_updates(
        dependency_groups,
        versions,
        exclude,
        only,
        allow_prerelease=prerelease,
        max_bump=max_bump,
    )
    logger.status("Resolved", f"{len(package_names)} packages in {elapsed_ms:.0f}ms")

    if not updates:
        logger.status("Audited", f"{len(package_names)} dependencies, all up to date")
        _emit_structured(output_format, [], [])
        if check:
            raise click.exceptions.Exit(0)
        return

    if check:
        _report_updates(output_format, updates, [], {}, filepath)
        logger.warning(f"{len(updates)} {_pluralize(len(updates))} can be upgraded")
        raise click.exceptions.Exit(1)

    if dry_run:
        _report_updates(output_format, updates, [], {}, filepath)
        logger.warning("Dry run enabled, no changes were written to pyproject.toml")
        return

    if no_lock:
        _write(pyproject, group, updates, filepath, all_groups=all_groups)
        _report_updates(output_format, updates, [], {}, filepath)
        return

    applied, held_back, conflicts = _apply_with_lock(
        pyproject,
        backup,
        dependency_groups,
        group,
        updates,
        filepath,
        versions,
        all_groups=all_groups,
        offline=offline,
        strict=strict,
        resolve=resolve,
        allow_prerelease=prerelease,
        max_bump=max_bump,
    )
    _report_updates(output_format, applied, held_back, conflicts, filepath)
    if applied:
        logger.status("Locked", "dependencies")


def _emit_structured(
    output_format: str,
    updated: list[parsers.Update],
    held_back: list[parsers.Update],
) -> None:
    if output_format != "text":
        click.echo(report.render(output_format, updated, held_back), color=False)


def _report_updates(
    output_format: str,
    updated: list[parsers.Update],
    held_back: list[parsers.Update],
    conflicts: dict[str, list[str]],
    filepath: pathlib.Path,
) -> None:
    if output_format != "text":
        _emit_structured(output_format, updated, held_back)
        return

    for update in updated:
        logger.update(update.name, update.old_version, update.new_version)
    if updated:
        logger.status("Updated", f"{len(updated)} {_pluralize(len(updated))} in {filepath.name}")
    for update in held_back:
        peers = conflicts.get(update.name)
        reason = f"conflicts with {', '.join(peers)}" if peers else "could not be resolved"
        logger.warning(
            f"Held back {update.name} v{update.old_version} -> v{update.new_version} ({reason})",
        )


def _write(
    pyproject: tomlkit.TOMLDocument,
    group: tuple[str, ...],
    updates: list[parsers.Update],
    filepath: pathlib.Path,
    *,
    all_groups: bool,
) -> None:
    document = parsers.apply_updates(pyproject, group, updates, all_groups=all_groups)
    with filepath.open("w") as toml_file:
        tomlkit.dump(document, toml_file)


def _try_lock(  # noqa: PLR0913
    pyproject: tomlkit.TOMLDocument,
    group: tuple[str, ...],
    updates: list[parsers.Update],
    filepath: pathlib.Path,
    *,
    all_groups: bool,
    offline: bool,
) -> exceptions.UVCommandError | None:
    _write(pyproject, group, updates, filepath, all_groups=all_groups)
    try:
        uv.lock(offline=offline, cwd=filepath.parent)
    except exceptions.UVCommandError as exception:
        return exception
    return None


def _apply_with_lock(  # noqa: PLR0913
    pyproject: tomlkit.TOMLDocument,
    backup: tomlkit.TOMLDocument,
    dependency_groups: list[tuple[str, items.Array]],
    group: tuple[str, ...],
    updates: list[parsers.Update],
    filepath: pathlib.Path,
    versions: dict[str, list[Version]],
    *,
    all_groups: bool,
    offline: bool,
    strict: bool,
    resolve: bool,
    allow_prerelease: bool,
    max_bump: str | None,
) -> tuple[list[parsers.Update], list[parsers.Update], dict[str, list[str]]]:
    """
    Apply the upgrades and lock, returning the applied, held-back and conflict info.

    The full set is tried first (the common, fast path). On failure, `--strict`
    rolls everything back, while the default best-effort mode keeps the maximal
    subset of upgrades that locks. With `--resolve`, an upgrade that does not lock
    at its latest version is bisected for the highest version that does.
    """
    error = _try_lock(pyproject, group, updates, filepath, all_groups=all_groups, offline=offline)
    if error is None:
        return updates, [], {}

    if strict:
        with filepath.open("w") as toml_file:
            tomlkit.dump(backup, toml_file)
        logger.error("Failed to lock the dependencies, rolling back changes", cause=error)
        raise click.exceptions.Exit(ERROR_EXIT_CODE)

    all_names = parsers.collect_all_names(dependency_groups)
    applied: list[parsers.Update] = []
    held_back: list[parsers.Update] = []
    conflicts: dict[str, list[str]] = {}

    for update in updates:
        error = _try_lock(
            pyproject, group, [*applied, update], filepath, all_groups=all_groups, offline=offline
        )
        if error is None:
            applied.append(update)
            continue

        if resolve:
            compatible = _search_compatible(
                pyproject,
                group,
                applied,
                update,
                versions,
                filepath,
                all_groups=all_groups,
                offline=offline,
                allow_prerelease=allow_prerelease,
                max_bump=max_bump,
            )
            if compatible is not None:
                applied.append(compatible)
                continue

        held_back.append(update)
        conflicts[update.name] = parsers.find_conflicts(
            error.stderr, all_names, canonicalize_name(update.name)
        )

    # The last trial may have written a failing candidate; restore the accepted set.
    _write(pyproject, group, applied, filepath, all_groups=all_groups)
    return applied, held_back, conflicts


def _search_compatible(  # noqa: PLR0913
    pyproject: tomlkit.TOMLDocument,
    group: tuple[str, ...],
    applied: list[parsers.Update],
    update: parsers.Update,
    versions: dict[str, list[Version]],
    filepath: pathlib.Path,
    *,
    all_groups: bool,
    offline: bool,
    allow_prerelease: bool,
    max_bump: str | None,
) -> parsers.Update | None:
    """Binary-search the eligible versions for the highest that locks with `applied`."""
    candidates = parsers.eligible_versions(
        update,
        versions.get(canonicalize_name(update.name), []),
        allow_prerelease=allow_prerelease,
        max_bump=max_bump,
    )

    # Candidates are ascending; the last is the latest version, which already failed.
    low, high = 0, len(candidates) - 2
    best: parsers.Update | None = None
    while low <= high:
        mid = (low + high) // 2
        candidate = parsers.at_version(update, candidates[mid])
        error = _try_lock(
            pyproject,
            group,
            [*applied, candidate],
            filepath,
            all_groups=all_groups,
            offline=offline,
        )
        if error is None:
            best = candidate
            low = mid + 1
        else:
            high = mid - 1
    return best


def _pluralize(count: int) -> str:
    return "dependency" if count == 1 else "dependencies"


def main() -> None:
    """Entry point that renders failures as uv-style errors instead of tracebacks."""
    try:
        exit_code = cli.main(standalone_mode=False)
    except click.exceptions.Abort as exception:
        logger.exception("operation cancelled")
        raise SystemExit(130) from exception
    except click.ClickException as exception:
        logger.exception(exception.format_message())
        raise SystemExit(exception.exit_code) from exception
    except exceptions.BaseError as exception:
        logger.exception(str(exception))
        raise SystemExit(ERROR_EXIT_CODE) from exception
    except Exception as exception:
        logger.exception(f"unexpected error: {exception}")
        if logger.verbose:
            raise
        raise SystemExit(ERROR_EXIT_CODE) from exception
    else:
        raise SystemExit(exit_code or 0)


if __name__ == "__main__":
    main()
