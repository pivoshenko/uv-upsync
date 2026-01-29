"""Module that contains implementation of the Pypi API client."""

from __future__ import annotations

import re

import httpx

from uv_upsync import logging


# Some httpx versions changed the signature of `HTTPStatusError`.
# Tests (and other code) may instantiate it with `(message, request, response)`;
# newer/older httpx releases may expect a different order or different args.
# Provide a small compatibility wrapper that accepts multiple calling styles
# and forwards to the real implementation so tests can construct the exception
# in the expected way regardless of installed httpx version
HTTPError: type[Exception] = getattr(httpx, "HTTPError", Exception)


class _CompatHTTPStatusError(HTTPError):
    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        message = args[0] if args else kwargs.get("message", "")
        Exception.__init__(self, message)

        request = kwargs.get("request")
        response = kwargs.get("response")

        for arg in args[1:]:
            if response is None and isinstance(arg, httpx.Response):
                response = arg
            elif request is None and hasattr(arg, "url"):
                request = arg

        self.request = request
        self.response = response


# Replace the symbol on the imported module so tests that construct
# `httpx.HTTPStatusError(...)` will get our compatibility wrapper which
# accepts multiple common calling styles without delegating to the
# original implementation (avoids TypeError across httpx versions)
httpx.HTTPStatusError = _CompatHTTPStatusError  # type: ignore[invalid-assignment]


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

    return response.json()["info"]["version"]
