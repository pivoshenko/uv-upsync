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
  <a href="https://github.com/astral-sh/uv">
    <img alt="uv" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json&style=flat-square&label=uv">
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

`uv-upsync` is `uv lock --upgrade` for the version specifiers you actually write.

`uv lock --upgrade` refreshes your **lockfile** but leaves the lower bounds in
`pyproject.toml` untouched, so `httpx>=0.24.0` stays `>=0.24.0` forever.
`uv-upsync` raises those human-authored bounds to the latest published version,
re-locks with `uv`, and rolls back if the resolution fails — all while
preserving your formatting, comments, operators, extras and environment markers.

### Features

- **Built for the uv ecosystem** — familiar flags (`--project`, `--upgrade-package`,
  `--all-groups`, `--offline`, `--no-cache`, `--color`), uv-style output and a
  `uv lock` round-trip with automatic rollback on failure
- **Index-aware** — resolves versions from the [PEP 691] index configured for
  your project via `[[tool.uv.index]]`, so private indexes work out of the box
- **Correct by construction** — specifiers are parsed with [`packaging`], the
  canonical PEP 440/508 implementation, not regular expressions
- **Conservative** — only raises lower bounds (`>=`, `>`, `~=`); pinned (`==`),
  capped (`<`, `<=`) and excluded (`!=`) constraints are left untouched
- **Format-preserving** — only the version token is rewritten; everything else,
  including comments and markers, is kept verbatim
- **Fast** — version lookups are fetched concurrently and cached
- **Selective** — target specific groups or packages, or exclude packages
- **Safe** — `--dry-run` to preview and `--check` for CI

## Installation

Run it without installing:

```shell
uvx uv-upsync
```

Or add it to your development dependencies:

```shell
uv add --dev uv-upsync
```

## Usage

By default, `uv-upsync` upgrades every dependency in the `pyproject.toml` found
in the current directory:

```shell
$ uv-upsync
Updated click v8.1.8 -> v8.2.1
Updated httpx v0.27.0 -> v0.28.1
Resolved 12 packages in 184ms
Updated 2 dependencies in pyproject.toml
Locked dependencies
```

Nothing to do is reported the way uv reports it:

```shell
$ uv-upsync
Resolved 12 packages in 121ms
Audited 12 dependencies, all up to date
```

### Options

| Option | Description |
| --- | --- |
| `--project <DIR>` | Path to the project directory containing the `pyproject.toml` |
| `--directory <DIR>` | Change to `DIR` before running |
| `-P`, `--upgrade-package <PKG>` | Allow upgrades for only the given package(s) |
| `--exclude <PKG>` | Package(s) to exclude from upgrading |
| `--group <NAME>` | Upgrade dependencies in the given group(s) only |
| `--all-groups` | Upgrade dependencies in all groups |
| `--index-url <URL>` | Base URL of the [PEP 691] package index (defaults to the project's uv index or PyPI) |
| `--offline` | Disable network access, using only cached data |
| `-n`, `--no-cache` | Avoid reading from or writing to the cache |
| `--dry-run` | Preview the upgrades without writing to `pyproject.toml` |
| `--check` | Exit with a non-zero status if any upgrades are available |
| `-q`, `--quiet` | Use quiet output |
| `-v`, `--verbose` | Use verbose output (shows skipped dependencies) |
| `--color <auto\|always\|never>` | Control the use of color in output |
| `-V`, `--version` | Show the version and exit |

`uv-upsync` understands all three dependency tables: `project.dependencies`,
`project.optional-dependencies`, and `dependency-groups` ([PEP 735]).

## Examples

### Preview the upgrades

```shell
uv-upsync --dry-run
```

### Upgrade a single package

```shell
uv-upsync --upgrade-package httpx
```

### Exclude packages

```shell
uv-upsync --exclude click --exclude ruff
```

### Upgrade specific groups

```shell
# Only the project dependencies
uv-upsync --group project

# A couple of named groups
uv-upsync --group test --group docs
```

### Fail CI when dependencies are stale

```shell
uv-upsync --check
```

`--check` writes nothing and exits with a non-zero status when upgrades are
available, which makes it easy to wire into a scheduled job or pre-merge gate.

[PEP 691]: https://peps.python.org/pep-0691
[PEP 735]: https://peps.python.org/pep-0735
[`packaging`]: https://packaging.pypa.io
