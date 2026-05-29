"""Module that contains tests for the module that contains the PyPI client."""

from __future__ import annotations

import typing

import httpx
import pytest

from packaging.version import Version

from uv_upsync import pypi


if typing.TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.mark.parametrize(
    ("pyproject", "expected"),
    [
        ({}, None),
        (
            {"tool": {"uv": {"index-url": "https://legacy.example/simple"}}},
            "https://legacy.example/simple",
        ),
        (
            {
                "tool": {
                    "uv": {
                        "index": [
                            {"url": "https://a.example"},
                            {"url": "https://b.example", "default": True},
                        ]
                    }
                }
            },
            "https://b.example",
        ),
        (
            {"tool": {"uv": {"index": [{"url": "https://first.example"}]}}},
            "https://first.example",
        ),
    ],
)
def test_index_url_from_pyproject(pyproject: dict, expected: str | None) -> None:
    assert pypi.index_url_from_pyproject(pyproject) == expected


def _mock_response(mocker: MockerFixture, versions: list[str]) -> typing.Any:  # noqa: ANN401
    response = mocker.Mock(spec=httpx.Response)
    response.json.return_value = {"versions": versions}
    response.raise_for_status.return_value = None
    return response


def test_fetch_versions_returns_sorted_parsed_versions(mocker: MockerFixture) -> None:
    client = pypi.PyPIClient()
    mocker.patch.object(
        client._client,
        "get",
        return_value=_mock_response(mocker, ["1.1.0", "1.0.0", "not-a-version", "2.0.0"]),
    )

    assert client.fetch_versions("Some-Package") == [
        Version("1.0.0"),
        Version("1.1.0"),
        Version("2.0.0"),
    ]
    client.close()


def test_fetch_versions_uses_canonical_name_in_url(mocker: MockerFixture) -> None:
    client = pypi.PyPIClient()
    mock_get = mocker.patch.object(
        client._client, "get", return_value=_mock_response(mocker, ["1.2.3"])
    )

    client.fetch_versions("Coverage")
    mock_get.assert_called_once_with("https://pypi.org/simple/coverage/")
    client.close()


def test_fetch_versions_caches_results(mocker: MockerFixture) -> None:
    client = pypi.PyPIClient()
    mock_get = mocker.patch.object(
        client._client, "get", return_value=_mock_response(mocker, ["1.0.0"])
    )

    assert client.fetch_versions("pkg") == [Version("1.0.0")]
    assert client.fetch_versions("pkg") == [Version("1.0.0")]
    mock_get.assert_called_once()
    client.close()


def test_fetch_versions_no_cache(mocker: MockerFixture) -> None:
    client = pypi.PyPIClient(no_cache=True)
    mock_get = mocker.patch.object(
        client._client, "get", return_value=_mock_response(mocker, ["1.0.0"])
    )

    client.fetch_versions("pkg")
    client.fetch_versions("pkg")
    assert mock_get.call_count == 2
    client.close()


def test_fetch_versions_offline_returns_empty(mocker: MockerFixture) -> None:
    client = pypi.PyPIClient(offline=True)
    mock_get = mocker.patch.object(client._client, "get")
    mocker.patch("uv_upsync.logging.Logger.skip")

    assert client.fetch_versions("pkg") == []
    mock_get.assert_not_called()
    client.close()


def test_fetch_versions_http_error_returns_empty(mocker: MockerFixture) -> None:
    client = pypi.PyPIClient()
    response = mocker.Mock(spec=httpx.Response)
    response.raise_for_status.side_effect = httpx.HTTPError("boom")
    mocker.patch.object(client._client, "get", return_value=response)
    mocker.patch("uv_upsync.logging.Logger.warning")

    assert client.fetch_versions("pkg") == []
    client.close()


def test_fetch_many(mocker: MockerFixture) -> None:
    client = pypi.PyPIClient()
    mocker.patch.object(
        client, "fetch_versions", side_effect=lambda name: [Version(f"1.{len(name)}.0")]
    )

    result = client.fetch_many(["A", "bb", "A"])
    assert result == {"a": [Version("1.1.0")], "bb": [Version("1.2.0")]}
    client.close()


def test_fetch_many_empty() -> None:
    client = pypi.PyPIClient()
    assert client.fetch_many([]) == {}
    client.close()


def test_client_context_manager(mocker: MockerFixture) -> None:
    with pypi.PyPIClient() as client:
        mock_close = mocker.patch.object(client._client, "close")
    mock_close.assert_called_once()
