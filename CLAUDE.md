# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

`uv-upsync` is a `uv`-native CLI that raises the **lower bounds** of dependency specifiers in `pyproject.toml` to the latest published versions, re-runs `uv lock`, and holds back or rolls back anything that fails to resolve. It is not a lockfile updater — `uv lock --upgrade` already does that but leaves `httpx>=0.24.0` at `>=0.24.0` forever. `uv-upsync` rewrites the human-authored bound while preserving formatting, comments, operators, extras and environment markers verbatim.

The same code ships three ways: a PyPI package (`uvx uv-upsync`), two pre-commit hooks (`.pre-commit-hooks.yaml`: `uv-upsync` and `uv-upsync-check`), and a composite GitHub Action (`action.yml`). Changing CLI flags or output shape affects all three — check `action.yml` and the README option tables when you touch the option list.

## Commands

All workflow lives in the `justfile`:

| Command | Runs |
| --- | --- |
| `just install` | `uv sync --all-groups --all-extras` |
| `just format` | `uvx pyupgrade --py310-plus` over all `.py` outside `.venv`, then `uvx ruff check --fix .`, then `uvx ruff format .` |
| `just lint` | `uvx ruff check .` and `uvx ty check .` (no `ruff format --check` — formatting is not gated) |
| `just test` | `uv run pytest .`, skipped if a `.no-tests` sentinel file exists |
| `just audit` | `uvx pip-audit` |
| `just check` | `lint` + `test` |
| `just update` | `uv lock --upgrade` then `uvx uv-upsync` (dogfoods itself) |

Single test: `uv run pytest tests/test_parsers.py::test_name -x --no-cov`. `--no-cov` is worth adding because `addopts` in `pyproject.toml` forces `--cov=src --cov-report=term-missing`, which is noise for one test. 127 tests currently.

CI (`.github/workflows/ci.yaml`) runs `just install`, `just lint`, `just audit`, `just test` on `ubuntu-24.04-arm` with Python 3.13. Note `audit` runs in CI but is not part of `just check`.

## Architecture

The CLI is a single Click command, `cli` in `src/uv_upsync/__main__.py` (~520 lines, the bulk of the logic). Every other module is a component it composes — read `__main__.py` first; the rest only makes sense as its parts.

**Flow inside `cli`:**

1. **Config layering** — `config.load_config` reads `[tool.uv-upsync]` into a frozen `Config`. Precedence is applied in `cli` as `value = value or settings.value`, i.e. CLI flag > config > default.
2. **Index resolution** — `pypi.index_url_from_pyproject` honors legacy `tool.uv.index-url` first, then the `[[tool.uv.index]]` entry marked `default`, then the first entry. Full chain: `--index-url` > `[tool.uv-upsync].index-url` > uv's index > PyPI. Private indexes work because uv's own config is read.
3. **Fetch** — `pypi.PyPIClient` speaks the PEP 691 simple JSON API (`Accept: application/vnd.pypi.simple.v1+json`) and fetches all candidates concurrently (`ThreadPoolExecutor`, `MAX_WORKERS = 8`). Fetch failures log a warning and yield an empty version list rather than raising.
4. **Plan** — `parsers.plan_updates` decides which bumps are safe, mutating nothing.
5. **Apply + lock loop** — `_apply_with_lock`, the safety model (below).
6. **Report** — `_report_updates` / `report.render`.

### The safety model (`_apply_with_lock`)

- **Fast path**: write every update, run `uv lock`. If it locks, done.
- **`--strict`**: any lock failure restores `backup` (a `copy.deepcopy` of the original document taken before any mutation) and exits `2`.
- **Default best-effort**: retry each update incrementally on top of the accepted set, keeping the maximal subset that locks. Failures are held back, and `parsers.find_conflicts` scans `uv lock` stderr for the names of other declared dependencies to attribute the conflict.
- **`--resolve`**: `_search_compatible` binary-searches the eligible versions (ascending, minus the latest which already failed) for the highest one that locks.

Every trial writes the file, so the loop ends with an explicit `_write` of the accepted set to undo the last failing candidate.

### Format preservation (`parsers.py`)

Specifiers are **parsed** with `packaging` (PEP 440/508) for correctness, but the rewrite in `_replace_version` is a surgical replacement of only the version token inside the original string, splitting on `;` to leave the environment marker untouched. Never rebuild the requirement string from a `Requirement` object — that discards the author's formatting.

Upgrade policy: only `>=`, `>`, `~=` (`UPGRADABLE_OPERATORS`) are raised, and only when the specifier has **exactly one** such clause. Anything containing `==` or `===` is skipped entirely; `<`, `<=`, `!=` become the residual `SpecifierSet` that a new version must still satisfy, so `>=1.2,<2.0` has its floor raised to the newest version under the cap. `--max-bump major|minor|patch` filtering happens in `_within_bump`; pre-releases are excluded unless `--prerelease`.

`iter_dependency_groups` yields **live tomlkit arrays** labelled `project`, `optional-dependencies.<name>`, `dependency-groups.<name>`; an `Update` locates its target by `(group, index)`. Inline-table dependencies are skipped.

### Output and errors

- `report.render` handles `json` and `markdown` only — anything not `"json"` falls through to markdown. Text output is produced by `logging.Logger` instead, as uv-style status lines (`Resolved`, `Updated`, `Audited`, `Locked`).
- **Invariant**: non-text formats keep stdout machine-parseable via `quiet=quiet or output_format != "text"` in `cli`. Preserve this if you add logger calls on the hot path.
- `logging.Logger` is a **singleton** (`__new__` caches `_instance`). `tests/conftest.py` has an autouse fixture resetting `Logger._instance` — any test that configures the logger relies on it.
- `uv.lock()` is the only shell-out and only ever runs `uv lock [--offline]`, raising `UVCommandError` with captured stdout/stderr. If uv's error format changes, `parsers.find_conflicts` and its tests are what break.
- `main()` is the sole place converting exceptions into `SystemExit`. Inside `cli`, raise `click.exceptions.Exit(ERROR_EXIT_CODE)` (2) for user-facing failures; `BaseError` subclasses bubble to `main()`. `--check` exits `1` when upgrades exist, `0` when clean; abort is `130`.
- `commands.Command` / `commands.HelpFormatter` restyle `--help` to mirror uv's clap output (bold headings, cyan option names).

## Conventions

- **Ruff `select = ["ALL"]`** with targeted ignores in `pyproject.toml`. Imports are `force-single-line = true`, `lines-after-imports = 2`, `length-sort-straight = true`, and `from __future__ import annotations` is required in every module (enforced by `required-imports`). Line length 100.
- **Type checker is `ty`** (Astral's), not mypy.
- **Docstrings** follow a fixed opener: modules use `Module that contains ...`, `__init__.py` uses `Package that contains ...`. `D101`/`D102`/`D103`/`D107` are ignored, so undocumented classes and functions are fine — but if you write a docstring, match the pattern.
- **Tests** mirror source: `tests/test_<module>.py` for `src/uv_upsync/<module>.py`. `tests/*.py` ignores `INP001, PLR2004, S101, SLF001`, so magic numbers and private access are expected. `pytest-mock`'s `MockerFixture` is the mocking style; its import goes under `if typing.TYPE_CHECKING`.
- **Commits** are Conventional Commits (see `CONTRIBUTING.md`); `cliff.toml` filters unconventional commits out of the changelog, so a malformed message silently disappears from release notes. Branches are `<type>/<short-description>`.

## Release and versioning

`__version__` in `src/uv_upsync/__init__.py` is derived at runtime via `importlib.metadata.version("uv-upsync")` — do not hardcode it. `pyproject.toml`'s `version` is the single source of truth, and the release workflow bumps it with `uv version`.

Releases are `workflow_dispatch` only (`.github/workflows/release.yaml`): git-cliff derives the next version from commits (overridable via workflow input), then the workflow commits `pyproject.toml` + `CHANGELOG.md`, tags `v<version>`, creates the GitHub release from the changelog, and publishes with `uv build` + `uv publish --trusted-publishing always`. Don't bump the version or edit `CHANGELOG.md` by hand.

## Python version caveat

`requires-python = ">=3.10"` and the classifiers advertise 3.10, but `[tool.ty.environment] python-version = "3.13"` and CI runs only 3.13 — nothing checks 3.10 compatibility. `typing.Self` needs 3.11+, so every module carries `from __future__ import annotations` and `Self` is imported only under `TYPE_CHECKING` (`pypi.py`); `logging.py` reaches it as `typing.Self` in a lazy annotation and a string `typing.cast`. Keep new `Self`/3.11+ runtime references out of module scope — nothing in CI will catch a regression.
