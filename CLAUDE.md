# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

`uv-upsync` is a `uv`-native CLI that raises the **lower bounds** of dependency specifiers in `pyproject.toml` to the latest published versions, then re-runs `uv lock` and rolls back if resolution fails. It is **not** a lockfile updater — `uv lock --upgrade` already does that. `uv-upsync` rewrites the human-authored bounds (`httpx>=0.24.0` → `httpx>=0.28.1`) while preserving formatting, comments, operators, extras, and environment markers verbatim.

The same code ships three ways: a PyPI package (`uvx uv-upsync`), a pre-commit hook (`.pre-commit-hooks.yaml`), and a composite GitHub Action (`action.yml`).

## Commands

All workflow lives in the `justfile`:

- `just install` — `uv sync --all-groups --all-extras`
- `just format` — `uvx pyupgrade --py310-plus` over `src` and `tests`, then `uvx ruff check --fix .`, then `uvx ruff format .`
- `just lint` — `uvx ruff check .`, `uvx ruff format --check .`, and `uvx ty check .`
- `just test` — `uvx pytest .` (config in `pyproject.toml`; runs with `--cov=src`)
- `just audit` — `uvx pip-audit`
- `just check` — `lint` + `test` (the CI gate)
- `just update` — `uvx uv-upsync` then `uv sync` (dogfoods itself)

Single test: `uvx pytest tests/test_parsers.py::test_name -x`.

`requires-python = ">=3.10"` but `[tool.ty.environment] python-version = "3.13"` — type-check target is 3.13 even though runtime support starts at 3.10. Don't use 3.11+-only syntax in runtime code.

## Architecture

The CLI is a single Click command in `src/uv_upsync/__main__.py:cli` that orchestrates everything; the rest of the package is the pieces it composes. Read `__main__.py` first — the others make sense only as the components it calls.

**Flow** (in `cli`):

1. **Config layering** — `config.load_config(pyproject)` reads `[tool.uv-upsync]`. Final precedence in `cli` is CLI flag > config > default; each option is `value = value or settings.value`.
2. **Index resolution** — `pypi.index_url_from_pyproject` honors `[[tool.uv.index]]` / legacy `tool.uv.index-url`, falling back to PyPI. Private indexes work out of the box because we read uv's config.
3. **Fetch** — `pypi.PyPIClient` (PEP 691 simple JSON, `Accept: application/vnd.pypi.simple.v1+json`) fetches all candidate versions concurrently (`ThreadPoolExecutor`, `MAX_WORKERS=8`).
4. **Plan** — `parsers.plan_updates` decides which bumps are safe. Only `>=`, `>`, `~=` are upgraded (`UPGRADABLE_OPERATORS`); `==`, `===`, `<`, `<=`, `!=` are never touched. Compound specifiers like `>=1.2,<2.0` have their floor raised to the latest version that still satisfies the cap and exclusions. `--max-bump` and `--prerelease` filter candidates.
5. **Apply + lock loop** — `_apply_with_lock` in `__main__.py` is the heart of the safety model:
   - **Fast path**: write all updates, `uv lock`. If it locks, done.
   - **`--strict`**: any lock failure restores `backup` (a deep copy of the original TOML) and exits non-zero.
   - **Default (best-effort)**: try each update incrementally on top of the accepted set; failures are held back and `parsers.find_conflicts` parses `uv lock` stderr to attribute the conflict to peers.
   - **`--resolve`**: when an upgrade fails at its latest version, `_search_compatible` binary-searches the eligible versions for the highest one that locks.

**Format preservation** is in `parsers.py`: specifiers are *parsed* with `packaging` (PEP 440/508) for correctness, but the rewrite is a surgical replacement of only the version token in the original string. Don't rebuild the requirement string from a `Requirement` object — that loses formatting.

**uv shell-out** is intentionally minimal: `uv.lock()` only ever runs `uv lock [--offline]` via `subprocess.run` and raises `UVCommandError` with captured stdout/stderr. Stderr is parsed by `parsers.find_conflicts` to attribute holdbacks — if you change `uv`'s error format expectations, update `find_conflicts` and its tests.

**Output**: `report.render` produces `text` / `json` / `markdown`. `text` is the human stream printed via `logging.Logger` (uv-style status lines: `Resolved`, `Updated`, `Audited`, `Locked`). Non-text formats suppress status lines (`quiet=quiet or output_format != "text"` in `cli`) so stdout stays machine-parseable — preserve that invariant if you add new logger calls in the hot path.

**Errors**: `main()` is the only place that catches exceptions and turns them into `SystemExit` with uv-style formatting. Inside `cli`, raise `click.exceptions.Exit(ERROR_EXIT_CODE)` (=2) for user-facing failures; `BaseError` subclasses bubble up to `main()`.

## Project conventions

- **Ruff `select = ["ALL"]`** with targeted ignores in `pyproject.toml`. `force-single-line = true` for imports, `lines-after-imports = 2`, `from __future__ import annotations` is **required** in every module (enforced by ruff `required-imports`).
- **Tests** live in `tests/test_<module>.py` mirroring `src/uv_upsync/<module>.py`. `tests/*.py` ignores `INP001, PLR2004, S101, SLF001` so private access and magic numbers are fine in tests.
- **Type checker is `ty`** (Astral's), not mypy.
- **Versioning**: `__version__` in `src/uv_upsync/__init__.py` and `version` in `pyproject.toml` must stay in sync. `cliff.toml` drives the changelog.

## Sibling-repo context

This repo sits in `~/Development/sources/` — see the parent `CLAUDE.md` for the full monorepo map. `uv-upsync` belongs to the `libs` group; cross-cutting changes across libs are fanned out from the root `justfile` (`just <verb>-libs`). It is consumed by other repos in that workspace via `just update` recipes.
