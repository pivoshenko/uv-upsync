<div align="center">
  <img alt="logo" src="https://github.com/pivoshenko/uv-upsync/blob/main/assets/logo.svg?raw=True" height=200>
</div>

<br>

<p align="center">
  <a href="https://opensource.org/licenses/MIT">
    <img alt="License" src="https://img.shields.io/pypi/l/uv-upsync?style=flat-square&logo=opensourceinitiative&logoColor=white&color=0A6847&label=License">
  </a>
  <a href="https://pypi.org/project/uv-upsync">
    <img alt="Python" src="https://img.shields.io/pypi/pyversions/uv-upsync?style=flat-square&logo=python&logoColor=white&color=4856CD&label=Python">
  </a>
  <a href="https://pypi.org/project/uv-upsync">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/uv-upsync?style=flat-square&logo=pypi&logoColor=white&color=4856CD&label=PyPI">
  </a>
  <a href="https://github.com/pivoshenko/uv-upsync/actions/workflows/ci.yaml">
    <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/pivoshenko/uv-upsync/ci.yaml?label=CI&style=flat-square&logo=githubactions&logoColor=white&color=0A6847">
  </a>
  <a href="https://codecov.io/gh/pivoshenko/uv-upsync">
    <img alt="Coverage" src="https://img.shields.io/codecov/c/gh/pivoshenko/uv-upsync?token=cqRQxVnDR6&style=flat-square&logo=codecov&logoColor=white&color=0A6847&label=Coverage">
  </a>
  <a href="https://docs.astral.sh/ruff">
    <img alt="Ruff" src="https://img.shields.io/badge/Style-ruff-black.svg?style=flat-square&logo=ruff&logoColor=white&color=D7FF64">
  </a>
  <a href="https://stand-with-ukraine.pp.ua">
    <img alt="StandWithUkraine" src="https://img.shields.io/badge/Support-Ukraine-FFC93C?style=flat-square&labelColor=07689F">
  </a>
</p>

## Overview

`uv-upsync` - is a tool for automated dependency updates and version bumping in `pyproject.toml`.

### Features

- Fully type-safe
- Automatically updates dependencies to their latest versions from PyPI
- Multiple dependency groups support - handles `project.dependencies`, `project.optional-dependencies`, and `dependency-groups`
- Selective group updates - target specific dependency groups for updates (e.g., only update project dependencies or specific optional-dependencies groups)
- Selective package exclusion - exclude specific packages from being updated
- Dry-run mode - preview changes without modifying files
- Safe updates - automatically runs `uv lock` after updates and rolls back on failure

## Installation

Proceed by installing the tool and running it:

```shell
uvx uv-upsync
```

Alternatively, you can add it into your development dependencies:

```shell
uv add --dev uv-upsync
# or
uv add uv-upsync --group dev
```

## Usage and Configuration

By default, `uv-upsync` updates all dependencies in the `pyproject.toml`:

```shell
uv-upsync
```

### Command-line Options

#### `filepath`

**Type**: `Path`

**Default**: `./pyproject.toml`

**Short flag**: `-f`

Specifies the path to the `pyproject.toml` file. If your project file is located elsewhere or has a different name, you can set this parameter.

#### `exclude`

**Type**: `str`

**Default**: `()`

**Multiple values**: `allowed`

Specifies packages to exclude from updating. You can provide multiple package names to prevent them from being updated.

#### `group`

**Type**: `str`

**Default**: `()`

**Multiple values**: `allowed`

Specifies which dependency group(s) to update. You can target specific groups like `project` (for project.dependencies), optional-dependencies names, or dependency-groups names. If not specified, all groups are updated. This is useful when you want to update only certain parts of your dependencies.

#### `dry-run`

**Type**: `bool`

**Default**: `false`

Enables preview mode where changes are displayed without modifying the `pyproject.toml` file. This is useful for reviewing what would be updated before applying changes.

## Examples

### Excluding specific packages

```shell
uv-upsync --exclude click

# Skipping 'click>=8.1.8' (excluded)
# Skipping 'httpx>=0.28.1' (no new version available)
# Skipping 'tomlkit>=0.13.3' (no new version available)
# Updating dependencies in 'dependency-groups' group
# Skipping 'python-semantic-release~=10.4.1' (no new version available)
# Skipping 'poethepoet>=0.37.0' (no new version available)
# Skipping 'pyupgrade>=3.21.0' (no new version available)
# Skipping 'ruff>=0.14.0' (no new version available)
# Skipping 'commitizen>=4.9.1' (no new version available)
# Skipping 'mypy>=1.18.2' (no new version available)
# Skipping 'ruff>=0.14.0' (no new version available)
# Skipping 'coverage[toml]>=7.10.7' (no new version available)
# Excluding dependency 'pytest'
# Skipping 'pytest==7.4.4' (no new version available)
# Skipping 'pytest-cov>=7.0.0' (no new version available)
# Skipping 'pytest-lazy-fixture>=0.6.3' (no new version available)
# Skipping 'pytest-mock>=3.15.1' (no new version available)
# Skipping 'pytest-sugar>=1.1.1' (no new version available)
# Skipping 'sh>=2.2.2' (no new version available)
# Skipping 'xdoctest>=1.3.0' (no new version available)
```

### Updating specific dependency groups

```shell
# Update only project dependencies
uv-upsync --group project

# Update only dev dependencies (assuming you have a 'dev' group)
uv-upsync --group dev

# Update multiple specific groups
uv-upsync --group project --group test

# Skipping 'optional-dependencies.dev' (skipping because not in specified groups)
# Skipping 'dependency-groups.test' (skipping because not in specified groups)
# Updating dependencies in 'project' group
# ...
```
