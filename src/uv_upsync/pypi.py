"""
Module that contains a PyPI client that speaks the PEP 691 simple JSON API.

The client returns the full list of published versions for a set of packages
from any PEP 691 compatible index. By default it talks to PyPI, but it honors
the index configured for the project via `[[tool.uv.index]]` / `tool.uv.index-url`,
which keeps uv-upsync aligned with uv's own index resolution. Choosing which
version to bump to (respecting caps, pre-release and bump policies) is left to
`parsers`, which has the specifier context.
"""

from __future__ import annotations

import contextlib

from concurrent import futures
from typing import TYPE_CHECKING
from typing import Any
from typing import Self

import httpx

from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion
from packaging.version import Version

from uv_upsync import __version__
from uv_upsync import logging


if TYPE_CHECKING:
    from collections.abc import Iterable


logger = logging.Logger()

DEFAULT_INDEX_URL = "https://pypi.org/simple"
SIMPLE_API_ACCEPT = "application/vnd.pypi.simple.v1+json"
MAX_WORKERS = 8
DEFAULT_TIMEOUT = 15.0


def index_url_from_pyproject(pyproject: dict[str, Any]) -> str | None:
    """Resolve the default index URL from uv's configuration, if present."""
    uv_config = pyproject.get("tool", {}).get("uv", {})

    legacy_index_url = uv_config.get("index-url")
    if legacy_index_url:
        return str(legacy_index_url)

    indexes = uv_config.get("index", [])
    for index in indexes:
        if index.get("default"):
            return str(index["url"])
    if indexes:
        return str(indexes[0].get("url"))

    return None


class PyPIClient:
    """Fetches the published versions of packages from a simple index."""

    def __init__(
        self,
        index_url: str = DEFAULT_INDEX_URL,
        *,
        offline: bool = False,
        no_cache: bool = False,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._index_url = index_url.rstrip("/")
        self._offline = offline
        self._cache: dict[str, list[Version]] | None = None if no_cache else {}
        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "Accept": SIMPLE_API_ACCEPT,
                "User-Agent": f"uv-upsync/{__version__}",
            },
        )

    def __enter__(self) -> Self:
        """Enter the client context."""
        return self

    def __exit__(self, *_: object) -> None:
        """Close the client on context exit."""
        self.close()

    def close(self) -> None:
        self._client.close()

    def fetch_versions(self, name: str) -> list[Version]:
        canonical_name = canonicalize_name(name)

        if self._cache is not None and canonical_name in self._cache:
            return self._cache[canonical_name]

        versions = self._fetch_versions_uncached(canonical_name)

        if self._cache is not None:
            self._cache[canonical_name] = versions
        return versions

    def fetch_many(self, names: Iterable[str]) -> dict[str, list[Version]]:
        unique_names = {canonicalize_name(name) for name in names}
        if not unique_names:
            return {}

        with futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results = executor.map(self.fetch_versions, unique_names)
            return dict(zip(unique_names, results, strict=True))

    def _fetch_versions_uncached(self, canonical_name: str) -> list[Version]:
        if self._offline:
            logger.skip(f"Skipping {canonical_name} (offline)")
            return []

        url = f"{self._index_url}/{canonical_name}/"
        try:
            response = self._client.get(url)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exception:
            logger.warning(f"Failed to fetch versions for {canonical_name}: {exception}")
            return []

        versions: list[Version] = []
        for raw in payload.get("versions", []):
            with contextlib.suppress(InvalidVersion):
                versions.append(Version(raw))
        return sorted(versions)
