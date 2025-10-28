"""Module that contains implementation of the Pypi API client."""

from __future__ import annotations

import re

import httpx

from uv_upsync import logging


logger = logging.Logger()


def get_dependency_base_name(dependency_name: str) -> str:
    regex_match = re.match(r"^(.*?)\[", dependency_name)
    match regex_match:
        case None:
            return dependency_name.strip()
        case _:
            return regex_match.group(1).strip()


def fetch_latest_dependency_version(dependency_name: str) -> str | None:
    dependency_base_name = get_dependency_base_name(dependency_name)
    response = httpx.get(f"https://pypi.org/pypi/{dependency_base_name}/json")
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exception:
        logger.exception(f"Failed to fetch latest version for {dependency_name!r}", exception)
        return None

    return response.json()["info"]["version"]  # type: ignore[no-any-return]
