<h1 align="left">
  <img src="assets/logo.svg" alt="" height="40" align="left" style="vertical-align: middle; margin-right: 12px;">
  uv-upsync
</h1>

<p align="left">
  <a href="https://pypi.org/project/uv-upsync">
    <img alt="Python" src="https://img.shields.io/pypi/pyversions/uv-upsync?style=flat-square&logo=python&logoColor=white&color=4856CD&label=Python">
  </a>
  <a href="https://pypi.org/project/uv-upsync">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/uv-upsync?style=flat-square&logo=pypi&logoColor=white&color=4856CD&label=PyPI">
  </a>
  <a href="https://github.com/pivoshenko/uv-upsync/actions/workflows/ci.yaml">
    <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/pivoshenko/uv-upsync/ci.yaml?label=CI&style=flat-square&logo=githubactions&logoColor=white&color=0A6847">
  </a>
  <a href="https://docs.astral.sh/ruff">
    <img alt="Ruff" src="https://img.shields.io/badge/Style-ruff-black.svg?style=flat-square&logo=ruff&logoColor=white&color=D7FF64">
  </a>
  <a href="https://stand-with-ukraine.pp.ua">
    <img alt="StandWithUkraine" src="https://img.shields.io/badge/Support-Ukraine-FFC93C?style=flat-square&labelColor=07689F">
  </a>
</p>

## Overview

`uv-upsync` is a [uv]-native tool for automated dependency updates and version bumping in `pyproject.toml`.

`uv lock --upgrade` refreshes your **lockfile** but leaves the lower bounds in `pyproject.toml` untouched, so `httpx>=0.24.0` stays `>=0.24.0` forever. `uv-upsync` raises those human-authored bounds to the latest published version, re-locks with `uv`, and rolls back if the resolution fails — all while preserving your formatting, comments, operators, extras and environment markers.

[uv]: https://github.com/astral-sh/uv

### Features

- **Built for the uv ecosystem** — familiar flags (`--project`, `--upgrade-package`, `--all-groups`, `--offline`, `--no-cache`, `--color`), uv-style output and a `uv lock` round-trip with automatic rollback on failure
- **Index-aware** — resolves versions from the [PEP 691] index configured for your project via `[[tool.uv.index]]`, so private indexes work out of the box
- **Correct by construction** — specifiers are parsed with [`packaging`], the canonical PEP 440/508 implementation, not regular expressions
- **Conservative** — only raises lower bounds (`>=`, `>`, `~=`); pinned (`==`) requirements are never touched
- **Range-aware** — compound specifiers like `>=1.2,<2.0` have their floor raised to the latest version that still satisfies the cap (`<2.0`) and any exclusions (`!=`)
- **Controlled** — `--max-bump patch|minor|major` holds back larger jumps (auto-apply minors, review majors), and `--prerelease` opts into pre-release versions
- **Format-preserving** — only the version token is rewritten; everything else, including comments and markers, is kept verbatim
- **Fast** — version lookups are fetched concurrently and cached
- **Selective** — target specific groups or packages, or exclude packages
- **Configurable** — persist defaults in a `[tool.uv-upsync]` table, overridable per run
- **Resilient** — by default an upgrade that does not resolve is held back individually instead of failing the whole run (`--strict` to opt out)
- **Safe** — `--dry-run` to preview and `--check` for CI
- **Scriptable** — `--format json` for tooling and `--format markdown` for pull request bodies
- **Integrated** — ships a [pre-commit] hook and a GitHub Action

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

> The examples below assume `uv-upsync` is installed. If it isn't, prefix any command with `uvx` to run it without installing (e.g. `uvx uv-upsync --dry-run`).

By default, `uv-upsync` upgrades every dependency in the `pyproject.toml` found in the current directory:

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

| Option                            | Description                                                                          |
| --------------------------------- | ------------------------------------------------------------------------------------ |
| `--project <DIR>`                 | Path to the project directory containing the `pyproject.toml`                        |
| `--directory <DIR>`               | Change to `DIR` before running                                                       |
| `-P`, `--upgrade-package <PKG>`   | Allow upgrades for only the given package(s)                                         |
| `--exclude <PKG>`                 | Package(s) to exclude from upgrading                                                 |
| `--group <NAME>`                  | Upgrade dependencies in the given group(s) only                                      |
| `--all-groups`                    | Upgrade dependencies in all groups                                                   |
| `--max-bump <level>`              | Limit upgrades to at most `patch`, `minor`, or `major`                               |
| `--prerelease`                    | Allow upgrading to pre-release versions                                              |
| `--index-url <URL>`               | Base URL of the [PEP 691] package index (defaults to the project's uv index or PyPI) |
| `--offline`                       | Disable network access, using only cached data                                       |
| `-n`, `--no-cache`                | Avoid reading from or writing to the cache                                           |
| `--dry-run`                       | Preview the upgrades without writing to `pyproject.toml`                             |
| `--check`                         | Exit with a non-zero status if any upgrades are available                            |
| `--strict`                        | Roll back every upgrade and fail if the result does not lock                         |
| `--no-lock`                       | Write the upgrades without running `uv lock`                                         |
| `--resolve`                       | When an upgrade does not lock, bump to the latest version that does                  |
| `-q`, `--quiet`                   | Use quiet output                                                                     |
| `-v`, `--verbose`                 | Use verbose output (shows skipped dependencies)                                      |
| `--format <text\|json\|markdown>` | Output format for the upgrade summary                                                |
| `--color <auto\|always\|never>`   | Control the use of color in output                                                   |
| `-V`, `--version`                 | Show the version and exit                                                            |

`uv-upsync` understands all three dependency tables: `project.dependencies`, `project.optional-dependencies`, and `dependency-groups` ([PEP 735]).

### Resolution

After bumping the specifiers, `uv-upsync` re-locks with `uv`. If the combined upgrade does not resolve, the default **best-effort** mode keeps the largest subset of upgrades that locks and reports which ones were held back (naming the conflicting dependency when it can) — so a single incompatible dependency never costs you the rest:

```console
$ uv-upsync
Resolved 2 packages in 153ms
Updated idna v2.0 -> v3.17
Updated 1 dependency in pyproject.toml
warning: Held back docutils v0.16 -> v0.23 (conflicts with sphinx)
Locked dependencies
```

With `--resolve`, an upgrade that does not lock at its latest version is bisected for the **latest version that does**, instead of being held back entirely:

```console
$ uv-upsync --resolve
Updated idna v2.0 -> v3.17
Updated numpy v1.20 -> v2.0.2   # 2.4.6 needs a newer Python; 2.0.2 is the latest that fits
Updated 2 dependencies in pyproject.toml
Locked dependencies
```

Use `--strict` to instead roll back every upgrade and fail (exit code `2`) if the result does not lock, or `--no-lock` to write the upgrades and skip locking entirely.

## Configuration

`uv-upsync` reads defaults from a `[tool.uv-upsync]` table in your `pyproject.toml`, so you don't have to repeat them on every run:

```toml
[tool.uv-upsync]
exclude = ["click", "ruff"]               # never upgrade these packages
group = ["project", "test"]               # only these groups (omit for all)
upgrade-package = ["httpx"]               # only these packages
all-groups = true                         # upgrade every group
max-bump = "minor"                        # hold back major upgrades
prerelease = false                        # allow pre-release versions
resolve = false                           # bisect for the latest version that locks
index-url = "https://example.com/simple"  # PEP 691 index to query
```

Settings are resolved with the precedence **command line > `[tool.uv-upsync]` > defaults**: passing a flag always overrides the matching setting. The index is resolved as `--index-url` > `[tool.uv-upsync].index-url` > `[[tool.uv.index]]` > PyPI.

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

`--check` writes nothing and exits with a non-zero status when upgrades are available, which makes it easy to wire into a scheduled job or pre-merge gate.

## Pre-commit

Add `uv-upsync` to your [pre-commit] configuration:

```yaml
repos:
  - repo: https://github.com/pivoshenko/uv-upsync
    rev: v2.3.2
    hooks:
      - id: uv-upsync
```

Two hooks are available:

- **`uv-upsync`** — upgrade the bounds in `pyproject.toml` and re-lock (runs `uv lock`, so `uv` must be on your `PATH`)
- **`uv-upsync-check`** — fail the commit if any dependency can be upgraded, without writing changes

## GitHub Action

Keep dependencies fresh on a schedule and open a pull request with the results:

```yaml
name: upgrade-dependencies
on:
  schedule:
    - cron: "0 6 * * 1" # every Monday
  workflow_dispatch:

jobs:
  upsync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - id: upsync
        uses: pivoshenko/uv-upsync@v2.3.2
        with:
          args: --all-groups --format markdown
      - uses: peter-evans/create-pull-request@v6
        with:
          commit-message: "build: upgrade dependencies"
          title: "build: upgrade dependencies"
          body: ${{ steps.upsync.outputs.summary }}
          branch: build/uv-upsync
```

With `--format markdown` the action's `summary` output is a ready-made pull request body (`⬆️ click 8.1.8 → 8.2.1 …`). To gate pull requests instead, run the action with `args: --check` and drop the pull request step.

| Input               | Description                                | Default |
| ------------------- | ------------------------------------------ | ------- |
| `args`              | Additional arguments passed to `uv-upsync` | `""`    |
| `version`           | Version of `uv-upsync` to run              | latest  |
| `working-directory` | Directory to run in                        | `.`     |

| Output    | Description                                |
| --------- | ------------------------------------------ |
| `summary` | The upgrade summary printed by `uv-upsync` |

[PEP 691]: https://peps.python.org/pep-0691
[PEP 735]: https://peps.python.org/pep-0735
[`packaging`]: https://packaging.pypa.io
[pre-commit]: https://pre-commit.com
