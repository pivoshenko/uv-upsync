"""Module that contains tests for the module that contains the PyPI client."""

from __future__ import annotations

import typing

import httpx
import pytest

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


@pytest.mark.parametrize(
    ("versions", "expected"),
    [
        (["1.0.0", "1.2.0", "1.1.0"], "1.2.0"),
        (["1.0.0", "2.0.0b1"], "1.0.0"),  # prefer stable over prerelease
        (["2.0.0b1", "2.0.0a1"], "2.0.0b1"),  # fall back to prerelease
        (["not-a-version", "1.0.0"], "1.0.0"),  # skip invalid
        (["not-a-version"], None),
        ([], None),
    ],
)
def test_select_latest_version(versions: list[str], expected: str | None) -> None:
    assert pypi.select_latest_version(versions) == expected


def _mock_response(mocker: MockerFixture, versions: list[str]) -> typing.Any:  # noqa: ANN401
    response = mocker.Mock(spec=httpx.Response)
    response.json.return_value = {"versions": versions}
    response.raise_for_status.return_value = None
    return response


def test_fetch_latest_success(mocker: MockerFixture) -> None:
    client = pypi.PyPIClient()
    mocker.patch.object(
        client._client, "get", return_value=_mock_response(mocker, ["1.0.0", "1.1.0"])
    )

    assert client.fetch_latest("Some-Package") == "1.1.0"
    client.close()


def test_fetch_latest_uses_canonical_name_in_url(mocker: MockerFixture) -> None:
    client = pypi.PyPIClient()
    mock_get = mocker.patch.object(
        client._client, "get", return_value=_mock_response(mocker, ["1.2.3"])
    )

    client.fetch_latest("Coverage[toml]".replace("[toml]", ""))
    mock_get.assert_called_once_with("https://pypi.org/simple/coverage/")
    client.close()


def test_fetch_latest_caches_results(mocker: MockerFixture) -> None:
    client = pypi.PyPIClient()
    mock_get = mocker.patch.object(
        client._client, "get", return_value=_mock_response(mocker, ["1.0.0"])
    )

    assert client.fetch_latest("pkg") == "1.0.0"
    assert client.fetch_latest("pkg") == "1.0.0"
    mock_get.assert_called_once()
    client.close()


def test_fetch_latest_no_cache(mocker: MockerFixture) -> None:
    client = pypi.PyPIClient(no_cache=True)
    mock_get = mocker.patch.object(
        client._client, "get", return_value=_mock_response(mocker, ["1.0.0"])
    )

    client.fetch_latest("pkg")
    client.fetch_latest("pkg")
    assert mock_get.call_count == 2
    client.close()


def test_fetch_latest_offline_returns_none(mocker: MockerFixture) -> None:
    client = pypi.PyPIClient(offline=True)
    mock_get = mocker.patch.object(client._client, "get")
    mocker.patch("uv_upsync.logging.Logger.skip")

    assert client.fetch_latest("pkg") is None
    mock_get.assert_not_called()
    client.close()


def test_fetch_latest_http_error_returns_none(mocker: MockerFixture) -> None:
    client = pypi.PyPIClient()
    response = mocker.Mock(spec=httpx.Response)
    response.raise_for_status.side_effect = httpx.HTTPError("boom")
    mocker.patch.object(client._client, "get", return_value=response)
    mocker.patch("uv_upsync.logging.Logger.warning")

    assert client.fetch_latest("pkg") is None
    client.close()


def test_fetch_many(mocker: MockerFixture) -> None:
    client = pypi.PyPIClient()
    mocker.patch.object(client, "fetch_latest", side_effect=lambda name: f"{name}-v")

    result = client.fetch_many(["A", "b", "A"])
    assert result == {"a": "a-v", "b": "b-v"}
    client.close()


def test_fetch_many_empty() -> None:
    client = pypi.PyPIClient()
    assert client.fetch_many([]) == {}
    client.close()


def test_client_context_manager(mocker: MockerFixture) -> None:
    with pypi.PyPIClient() as client:
        mock_close = mocker.patch.object(client._client, "close")
    mock_close.assert_called_once()
