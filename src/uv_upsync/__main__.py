"""Module that contains the main entry point for the uv-upsync."""

from __future__ import annotations

import copy
import pathlib

import click
import tomlkit

from uv_upsync import commands
from uv_upsync import logging
from uv_upsync import parsers
from uv_upsync import uv


logger = logging.Logger()


@click.command(cls=commands.Command)
@click.option(
    "-f",
    "--filepath",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
    default=pathlib.Path.cwd() / "pyproject.toml",
    help=f"Filepath to the pyproject.toml file "
    f"(default: {click.style('./pyproject.toml', fg='magenta')})",
)
@click.option(
    "--exclude",
    type=click.STRING,
    multiple=True,
    default=(),
    help="Packages to exclude from updating "
    f"({click.style('multiple values allowed', fg='magenta')})",
)
@click.option(
    "--group",
    type=click.STRING,
    multiple=True,
    default=(),
    help="Specific dependency group(s) to update. Can be 'project', optional-dependencies names, "
    f"or dependency-groups names ({click.style('multiple values allowed', fg='magenta')}). "
    "If not specified, all groups are updated.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    type=click.BOOL,
    default=False,
    help="Preview changes without writing to pyproject.toml",
)
def main(  # noqa: C901, PLR0912, PLR0915
    filepath: pathlib.Path,
    exclude: tuple[str, ...],
    group: tuple[str, ...],
    *,
    dry_run: bool,
) -> None:
    """uv-upsync - is a tool for automated dependency updates and version bumping in pyproject.toml."""  # noqa: E501
    with filepath.open() as toml_file:
        pyproject = tomlkit.load(toml_file)
        bk_pyproject = copy.deepcopy(pyproject)

    dependencies_groups = parsers.get_dependencies_groups(pyproject)

    for group_name, dependency_group in dependencies_groups.items():
        match group_name:
            case "project":
                match group:
                    case () if not group:
                        pass
                    case _ if "project" in group:
                        pass
                    case _:
                        logger.warning("Skipping 'project' dependencies")
                        continue

                updated_dependency_specifiers = parsers.update_dependency_specifiers(
                    dependency_group,
                    exclude,
                )
                dependency_specifiers = pyproject["project"]["dependencies"]  # type: ignore[index]
                for index in range(len(dependency_specifiers)):  # type: ignore[arg-type]
                    dependency_specifiers[index] = updated_dependency_specifiers[index]  # type: ignore[index]

            case "optional-dependencies":
                dependency_groups = pyproject["project"][group_name]  # type: ignore[index]
                for subgroup_name, dependency_specifiers in dependency_groups.items():  # type: ignore[union-attr]
                    match group:
                        case () if not group:
                            pass
                        case _ if subgroup_name in group:
                            pass
                        case _:
                            logger.warning(f"Skipping 'optional-dependencies.{subgroup_name}'")
                            continue

                    updated_dependency_specifiers = parsers.update_dependency_specifiers(
                        dependency_specifiers,
                        exclude,
                    )
                    for index in range(len(dependency_specifiers)):
                        dependency_specifiers[index] = updated_dependency_specifiers[index]

            case "dependency-groups":
                dependency_groups = pyproject[group_name]
                for subgroup_name, dependency_specifiers in dependency_groups.items():  # type: ignore[union-attr]
                    match group:
                        case () if not group:
                            pass
                        case _ if subgroup_name in group:
                            pass
                        case _:
                            logger.warning(f"Skipping 'dependency-groups.{subgroup_name}'")
                            continue

                    updated_dependency_specifiers = parsers.update_dependency_specifiers(
                        dependency_specifiers,
                        exclude,
                    )
                    for index in range(len(dependency_specifiers)):
                        dependency_specifiers[index] = updated_dependency_specifiers[index]
            case _:
                pass

    match dry_run:
        case True:
            logger.warning(
                "Dry run mode enabled, no changes will be made to the pyproject.toml file",
            )
        case False:
            with filepath.open("w") as toml_file:
                tomlkit.dump(pyproject, toml_file)

            try:
                logger.info("Resolving dependencies...")
                uv.lock()
                logger.info("Dependencies resolved")
            except Exception as exception:
                logger.exception(
                    "Failed to lock the dependencies. Rolling back changes",
                    exception,
                )
                with filepath.open("w") as toml_file:
                    tomlkit.dump(bk_pyproject, toml_file)


if __name__ == "__main__":
    main()
