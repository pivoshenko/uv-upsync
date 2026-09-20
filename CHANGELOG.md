# Changelog

All notable changes to this project will be documented in this file.

## [2.4.2] - 2026-09-20

### Bug fixes

- Import Self from typing-extensions for python 3.10
- Import Self under TYPE_CHECKING to restore Python 3.10 support
- **commands**: Widen write_dl rows annotation to Iterable

### Build

- Bump python to 3.14
- Update dependencies
- Update dependencies
- Update dependencies
- **deps**: Update dependency lockfile
- **deps**: Update dependencies
- **deps**: Update dependencies

### CI/CD

- Pin workflow python to 3.14 and rename action.yml to yaml
- Pin setup-uv to v10.1.0
- Drop label sync in favor of terraform
- Publish to pypi via trusted publishing instead of a token
- Ignore rules newly stabilized in ruff 0.16
- Drop ruff format --check from lint; suppress more ty rules
- Use uv run pytest for project venv; format example file
- Fix action versions and test recipe failures
- Drop hashFiles guard; move .no-tests sentinel handling into justfile
- Flatten to one job per language
- Bump action versions to latest major
- Standardize workflow to per-language parallel pipelines on ubuntu-24.04-arm

### Documentation

- Use absolute raw url for logo and refresh version notes
- Rewrite CLAUDE.md from scratch
- Regenerate CLAUDE.md and add AGENTS.md
- **release**: Drop trusted publishing header comments
- Add pull request template
- Shorten module docstring to fit the line-length limit
- Regenerate CLAUDE.md
- Document the module docstring convention
- Normalize module and package docstrings
- Normalize punctuation and drop AI-flavored phrasing
- Refresh CLAUDE.md for current justfile + CI shape
- **ci**: Document required secrets at top of workflow files

### Miscellaneous

- **assets**: Drop svg repo attribution comments
- Repository housekeeping
- Symlink AGENTS.md to CLAUDE.md
- Remove local pull request template
- **deps**: Update locked dependencies
- Update dependency lockfile
- Add editorconfig
- **justfile**: Use uv lock --upgrade for update, scope pyupgrade to . excluding .venv
- Standardize justfile recipes and refresh CLAUDE.md

### Refactor

- **justfile**: Standardize recipe names and ordering

## [2.4.1] - 2026-05-31

### Build

- Bump deps, drop py3.9 and semantic-release tooling

### CI/CD

- Rework release, ci and labels pipelines

### Documentation

- Refresh readme, contributing and supporting docs

### Miscellaneous

- Drop vhs demo and gh issue templates

### Refactor

- Tidy logging and parser internals

### Release

- V2.4.1

## [2.4.0] - 2026-05-30

### Bug fixes

- **ci**: Configure ty python-version to match ruff target
- Replace singleton metaclass with __new__-based singleton

### Build

- Update dev dependencies
- Update dev dependencies
- Drop unused pytest-lazy-fixture (incompatible with pytest 9)
- Bump pytest to 9.0.3 to fix GHSA-6w46-j5rx-g56g
- Update dev dependencies
- Update dev dependencies
- Update dev dependencies

### Documentation

- Clearer tagline
- Drop manual table of contents in favor of github's built-in
- Reorder badges, add table of contents, simplify overview
- Note that examples can be run with uvx without installing

### Features

- Resolver-aware --resolve, conflict naming, and a VHS demo
- Add --format json/markdown output and expose it from the action
- Support compound ranges, --max-bump, and --prerelease
- Best-effort resolution that isolates un-lockable upgrades
- Add [tool.uv-upsync] config, pre-commit hook, and GitHub Action
- Render failures as uv-style errors instead of tracebacks
- Align uv-upsync with the uv ecosystem

### Miscellaneous

- Keep dependencies-upgrade and packaging-upgrade keywords
- Align pyproject keywords with github repository topics

## [2.3.2] - 2026-03-29

### Documentation

- Remove TOC

### Miscellaneous

- Remove deprecated GitHub workflows and files

## [2.3.1] - 2026-03-29

### Build

- Update dependencies

### Documentation

- Update badge

## [2.3.0] - 2026-03-29

### Build

- Update dependencies
- Update dependencies
- Update dev dependencies

### Refactor

- Run ty

## [2.2.0] - 2026-03-08

### Bug fixes

- Update metadata

### Build

- Update dev dependencies
- Update dev dependencies

### Miscellaneous

- Update chore files

## [2.1.0] - 2026-01-29

### Bug fixes

- Add compatibility wrapper for HTTPStatusError

### Build

- Replace mypy with ty

## [2.0.3] - 2026-01-10

### Build

- Update dev dependencies
- Update dev dependencies
- Update dev dependencies
- Update dev dependencies
- Update dev dependencies

### CI/CD

- Upgrade actions
- Update version of the Checkout action
- Update semantic release action version

### Documentation

- Update license

## [2.0.2] - 2025-11-02

### Documentation

- Update contribution instructions for testing and formatting commands

## [2.0.1] - 2025-11-02

### Build

- Update dev dependencies

### CI/CD

- Remove force option from semantic release configuration

### Miscellaneous

- Update .gitignore
- Update Commitizen config

### Style

- Sort metadata keys

## [2.0.0] - 2025-10-28

### Build

- Downgrade Pytest
- Update dev dependencies
- Update dev dependencies

### CI/CD

- Remove unused pytest option from configuration
- Update codecov action version

### Documentation

- Update notes

### Features

- Rename project from uv-plugin-up to uv-upsync and update related assets
- Add support for updating specific dependency groups

## [1.1.2] - 2025-10-11

### Documentation

- Update notes

## [1.1.1] - 2025-10-11

### Documentation

- Remove TOC
- Update notes

### Miscellaneous

- Update pyproject.toml with metadata, keywords, and classifiers

## [1.1.0] - 2025-10-11

### Bug fixes

- Enhance help text for package exclusion option to indicate multiple values are allowed

### Miscellaneous

- Update Coverage config

## [1.0.0] - 2025-10-11

### Bug fixes

- Update main function docstring for clarity

### CI/CD

- Add workflows

### Documentation

- Add logo

### Features

- Initial commit

### Miscellaneous

- Update ruff configuration and improve exception handling

### Refactor

- Implement singleton pattern for Logger class

### Testing

- Add comprehensive test suite for uv-plugin-up

