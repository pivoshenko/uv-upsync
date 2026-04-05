# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

uv-upsync is a CLI tool for automated dependency updates and version bumping in `pyproject.toml` files. It queries PyPI for latest versions and updates version specifiers while preserving TOML formatting, comments, and operators. Built with Click, httpx, and tomlkit.

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

- **`__main__.py`** — CLI definition and main orchestration: load pyproject.toml, iterate dependency groups, update specifiers, write back, run `uv lock`, rollback on failure
- **`parsers.py`** — TOML parsing, dependency specifier extraction, version update logic. Handles three group types: `project.dependencies`, `project.optional-dependencies`, `dependency-groups` (PEP 735). Skips `==`, `<=`, `<` operators (conservative). Preserves environment markers and inline tables
- **`pypi.py`** — httpx client to fetch latest versions from `https://pypi.org/pypi/{package}/json`. Strips extras from package names (e.g., `coverage[toml]` → `coverage`)
- **`uv.py`** — Subprocess wrapper for `uv lock`
- **`commands.py`** — Custom Click command/formatter classes for rich CLI output
- **`logging.py`** — Singleton logger using Click's echo
- **`exceptions.py`** — Custom exception hierarchy

## Code Conventions

- `from __future__ import annotations` required in every file (enforced by ruff isort)
- Python 3.13 target for ruff; requires-python >= 3.10
- All ruff lint rules enabled (`select = ["ALL"]`), specific ignores in pyproject.toml
- Line length: 100
- Double quotes, single-line imports, imports sorted by length
- Uses Python 3.10+ `match` statements extensively
- Type annotations throughout; type checker is `ty` (not mypy)
- Coverage target: 95%

## Commit Convention

Conventional Commits: `type(scope): description`

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `build`, `perf`, `style`, `revert`. Semantic-release uses these for automatic versioning (`feat` = major, `fix`/`perf`/`refactor` = minor, `docs`/`style` = patch).
