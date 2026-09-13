# uv-upsync

## What This Is

A single-command CLI that raises the **lower bounds of dependency specifiers in `pyproject.toml`** to the latest published versions, then re-locks with `uv`.

The distinction that defines the whole project: `uv lock --upgrade` refreshes the **lockfile** but leaves `httpx>=0.24.0` written as `>=0.24.0` forever. `uv-upsync` rewrites the human-authored bound in `pyproject.toml` itself, and does so surgically - only the version token is replaced, so operators, extras, environment markers, spacing and comments survive verbatim.

Published to PyPI as `uv-upsync`. `README.md` owns the option table, the `[tool.uv-upsync]` keys and the usage examples.

## Distribution Surfaces

Any change to the CLI flags has to land in four places, not one:

1. `src/uv_upsync/__main__.py` - the click options
2. `README.md` - the options table and the `[tool.uv-upsync]` example block
3. `action.yml` - the composite GitHub Action (passes `inputs.args` through to `uvx uv-upsync`, captures stdout into a `summary` output for PR bodies)
4. `.pre-commit-hooks.yaml` - the `uv-upsync` and `uv-upsync-check` hooks, both `pass_filenames: false` and gated on `^pyproject\.toml$`

A new config key also needs a branch in `config.load_config` plus its validator, and the corresponding `flag = flag or settings.flag` line in `cli`.

## Invariants Worth Knowing Before Editing

- **Only lower bounds are raised.** `UPGRADABLE_OPERATORS = {">=", ">", "~="}`; `==`/`===` are never touched, and a specifier with more or fewer than exactly one lower-bound clause is skipped entirely. This conservatism mirrors uv's `--upgrade` and is deliberate
- **Compound specifiers keep their cap.** `upgradable_specifier` splits off a residual `SpecifierSet` (the `<2.0`, the `!=`s) that every candidate version must still satisfy
- **`_replace_version` is a token swap, not a re-serialization.** It partitions on `;` to protect markers, then does a single `str.replace` from the operator onward. Do not "improve" this into a `str(Requirement)` round-trip - that would normalize the author's formatting, which is exactly what the tool promises not to do
- **Settings precedence is CLI > `[tool.uv-upsync]` > defaults**, implemented in `cli` as `flag = flag or settings.flag`. This means a falsy CLI value cannot override a truthy config value, which is intended for the flag-shaped options
- **The lock strategy has three modes.** The full upgrade set is tried first. On failure: `--strict` restores the deep-copied `backup` document and exits 2; the default best-effort mode re-locks incrementally to keep the maximal subset that resolves; `--resolve` additionally binary-searches `eligible_versions` for the highest version of a failing package that does lock. `_apply_with_lock` always rewrites the accepted set at the end, because the last trial may have left a failing candidate on disk
- **Exit codes:** `0` success, `1` from `--check` when upgrades exist, `2` (`ERROR_EXIT_CODE`) for any error. `main()` catches everything and renders uv-style `error:` lines instead of tracebacks, re-raising the traceback only under `--verbose`
- **Non-text `--format` implies quiet.** `logger.configure(quiet=quiet or output_format != "text", ...)` keeps stdout parseable

## Architecture

Single flow, no plugin system, no async. `__main__.py` is the orchestrator and everything else is a leaf module it calls.

```
__main__.cli
  -> config.load_config      read [tool.uv-upsync] defaults
  -> parsers.iter_dependency_groups   locate the live tomlkit arrays
  -> pypi.PyPIClient.fetch_many       concurrent PEP 691 lookups
  -> parsers.plan_updates             compute the bumps (pure, no mutation)
  -> __main__._apply_with_lock        write + `uv lock`, with fallback strategies
  -> report.render / logging.Logger   emit the summary
```

The module boundaries that carry a rule (the rest is `ls src/uv_upsync/`):

- `__main__.py` owns the entire click command surface - every flag is declared there - plus the write/lock/rollback orchestration
- `parsers.py` owns all TOML and specifier logic: group iteration, requirement parsing, eligibility, bump policy, surgical rewrite, conflict extraction from uv's stderr
- `report.py` is JSON and Markdown renderers only - text output belongs to `logging.Logger`, not to this module

## Commands

`just --list` and `CONTRIBUTING.md` carry the recipe table; CI runs the same recipes, so a green `just check` locally means a green CI. Two things the table does not say:

- `just format` and `just lint` invoke ruff and ty via `uvx`, not from the project venv, so they resolve the latest release rather than the pinned one in `[dependency-groups]`. Version skew between the two is expected and occasionally shows up as new lint findings
- `just update` runs `uvx uv-upsync` against this repo - the tool eats its own dogfood here

Run the CLI itself with `uv run uv-upsync ...` (entry point `uv_upsync.__main__:main`).

## Conventions

- Module docstrings follow the house phrasing `"""Module that contains ..."""`. Docstrings take sentence punctuation; code comments never end with a period
- **Tests mirror modules one-to-one** - `tests/test_<module>.py`. Mocking is `pytest-mock`'s `mocker` fixture, never `unittest.mock` directly. `conftest.py` resets `Logger._instance` between tests via an autouse fixture, because the logger is a process-wide singleton
- Everything else - ruff select and ignores, import style, line length, pytest `addopts` - lives in `pyproject.toml` and is enforced by `just lint`. Add a targeted `# noqa: RULE` at the site (as `__main__.cli` does) rather than widening the global ignores

## Release

Fully automated - **do not bump the version in `pyproject.toml` by hand.** The `Release` workflow is `workflow_dispatch` only; git-cliff derives the next version from the commit history (or takes the `version` input), `uv version` writes it, `CHANGELOG.md` is regenerated, the tag is pushed, and PyPI publication goes through trusted publishing.

This makes **Conventional Commits load-bearing**: `cliff.toml` sets `filter_unconventional = true`, so a commit that doesn't match a known prefix is dropped from the changelog entirely, and `features_always_bump_minor` / `breaking_always_bump_major` decide the version. Use `<type>(<scope>): <subject>` with scopes like `parsers`, `pypi`, `config`, `cli`. `CONTRIBUTING.md` has the full prefix table, the branch pattern and the CI/CD workflow table.

`AGENTS.md` is a symlink to this file - edit `CLAUDE.md`, never the symlink.
