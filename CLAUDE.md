# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

uv-upsync is a CLI tool for automated dependency updates and version bumping in `pyproject.toml` files. Think of it as `uv lock --upgrade` for the human-authored version specifiers: it raises the lower bounds in `pyproject.toml` to the latest published versions, then re-locks with `uv`. It is designed to feel native to the uv ecosystem — uv-style flags, output, and a `uv lock` round-trip with rollback on failure. Built with Click, httpx, tomlkit, and packaging.

## Commands

All commands use `uv run` (no virtual env activation needed). Task runner: `just`.

```bash
just format          # pyupgrade + ruff format
just lint            # ty check + ruff check
just test            # pytest with coverage
just update          # uv lock --upgrade + uv-upsync

uv run pytest tests/test_parsers.py              # single test file
uv run pytest tests/test_parsers.py::test_name   # single test
uv run ruff check --no-fix .                     # lint without auto-fix
uv run ty check .                                # type check
```

## Architecture

Entry point: `uv_upsync.__main__:main` (Click CLI).

Source in `src/uv_upsync/` with clear separation:

- **`__main__.py`** — uv-style Click CLI and orchestration. Resolves the target pyproject, collects upgradable package names across the selected groups, fetches latest versions concurrently, plans updates, then locks. Default is **best-effort**: try the full set, and on a lock failure keep the maximal subset that resolves (greedy), naming the conflicting peer (via `find_conflicts`) for held-back packages. `--resolve` bisects a held-back dependency's versions for the latest that locks; `--strict` rolls back everything and exits 2; `--no-lock` writes without locking. Supports `--check` (CI gate) and `--dry-run`
- **`parsers.py`** — TOML iteration and version-bumping logic. Parses specifiers with `packaging` (`Requirement`/`Specifier`), not regex. `upgradable_specifier` returns the single raisable lower-bound clause plus a residual `SpecifierSet` (caps/exclusions), so compound ranges like `>=1.2,<2.0` are supported. `select_new_version` picks the highest version that beats the floor, satisfies the residual, and respects `--prerelease`/`--max-bump`. `plan_updates` computes a list of `Update`s (group label, index, new text) without mutating; `apply_updates` returns a deep-copied document with a chosen subset applied. Handles `project.dependencies`, `project.optional-dependencies`, `dependency-groups` (PEP 735). Only raises lower bounds (`>=`, `>`, `~=`); pinned (`==`) requirements are never touched. `_replace_version` rewrites only the version token, preserving formatting, extras and markers. Inline tables (e.g. `include-group`) are ignored
- **`pypi.py`** — `PyPIClient` querying the PEP 691 simple JSON API (`Accept: application/vnd.pypi.simple.v1+json`). Index-aware: `index_url_from_pyproject` reads `[[tool.uv.index]]` / `tool.uv.index-url`. Fetches concurrently (thread pool), caches in memory, supports `--offline`/`--no-cache`. Picks the highest stable version via `packaging.version`
- **`report.py`** — Renders the applied/held-back updates as JSON or Markdown for `--format` (text output is handled by the logger). The GitHub Action exposes the Markdown as a `summary` output for PR bodies
- **`uv.py`** — Subprocess wrapper for `uv lock` (accepts `cwd` and `--offline`)
- **`config.py`** — Reads `[tool.uv-upsync]` from pyproject (`exclude`, `group`, `upgrade-package`, `all-groups`, `index-url`) with validation. CLI args take precedence over config, which takes precedence over defaults
- **`commands.py`** — Custom Click command/formatter classes; help mirrors uv's clap layout (bold headers, cyan flags)
- **`logging.py`** — Singleton logger with uv-style output: `status` (green verb), `update` (`Updated <name> v<old> -> v<new>`), `warning:`/`error:` prefixes to stderr (with dimmed `Caused by:` chains), verbose-only `skip`. Honors `--quiet`/`--verbose`/`--color`
- **`exceptions.py`** — `BaseError` and `UVCommandError`

The entry point (`main`) wraps the Click command so failures render as `error:` lines (never tracebacks). Repo root also ships `.pre-commit-hooks.yaml` and a composite `action.yml`.

## Code Conventions

- `from __future__ import annotations` required in every file (enforced by ruff isort)
- Python 3.13 target for ruff; requires-python >= 3.10
- All ruff lint rules enabled (`select = ["ALL"]`), specific ignores in pyproject.toml
- Line length: 100
- Double quotes, single-line imports, imports sorted by length
- Type annotations throughout; type checker is `ty` (not mypy)
- Coverage target: 95% (`__main__.py` and `__init__.py` are omitted from coverage)
- Run the test suite with all dependency groups installed (e.g. `uv run --all-groups pytest`) so `pytest-cov` is available

## Commit Convention

Conventional Commits: `type(scope): description`

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `build`, `perf`, `style`, `revert`. Semantic-release uses these for automatic versioning (`feat` = major, `fix`/`perf`/`refactor` = minor, `docs`/`style` = patch).
