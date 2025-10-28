"""Module that contains tests for the model that contains implementation of the Pypi API client."""

from __future__ import annotations

import typing

import httpx
import pytest


if typing.TYPE_CHECKING:
    from pytest_mock import MockerFixture

from uv_upsync import pypi


@pytest.mark.parametrize(
    ("dependency_name", "expected_base_name"),
    [
        ("package", "package"),
        ("package[extra]", "package"),
        ("package[extra1,extra2]", "package"),
        ("package-name", "package-name"),
        ("package_name", "package_name"),
        ("package-name[extra]", "package-name"),
        ("  package  ", "package"),
        ("  package[extra]  ", "package"),
    ],
)
def test_get_dependency_base_name(dependency_name: str, expected_base_name: str) -> None:
    base_name = pypi.get_dependency_base_name(dependency_name)
    assert base_name == expected_base_name


@pytest.mark.parametrize(
    ("dependency_name", "mock_response_data", "expected_version"),
    [
        ("requests", {"info": {"version": "2.31.0"}}, "2.31.0"),
        ("click", {"info": {"version": "8.1.7"}}, "8.1.7"),
        ("httpx[http2]", {"info": {"version": "0.28.1"}}, "0.28.1"),
        ("package-name", {"info": {"version": "1.0.0"}}, "1.0.0"),
    ],
)
def test_fetch_latest_dependency_version_success(
    mocker: MockerFixture,
    dependency_name: str,
    mock_response_data: dict[str, dict[str, str]],
    expected_version: str,
) -> None:
    mock_response = mocker.Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None

    mocker.patch("httpx.get", return_value=mock_response)

    version = pypi.fetch_latest_dependency_version(dependency_name)
    assert version == expected_version


@pytest.mark.parametrize(
    ("dependency_name", "status_code", "error_type"),
    [
        ("nonexistent-package", 404, httpx.HTTPStatusError),
        ("another-package", 500, httpx.HTTPStatusError),
        ("forbidden-package", 403, httpx.HTTPStatusError),
    ],
)
def test_fetch_latest_dependency_version_http_error(
    mocker: MockerFixture,
    dependency_name: str,
    status_code: int,
    error_type: type[Exception],
) -> None:
    mock_response = mocker.Mock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.raise_for_status.side_effect = error_type(
        "Error",
        request=mocker.Mock(),
        response=mock_response,
    )

    mocker.patch("httpx.get", return_value=mock_response)
    mocker.patch("uv_upsync.logging.Logger.exception")

    version = pypi.fetch_latest_dependency_version(dependency_name)
    assert version is None


def test_fetch_latest_dependency_version_with_extras(mocker: MockerFixture) -> None:
    mock_response = mocker.Mock(spec=httpx.Response)
    mock_response.json.return_value = {"info": {"version": "1.2.3"}}
    mock_response.raise_for_status.return_value = None

    mock_get = mocker.patch("httpx.get", return_value=mock_response)

    version = pypi.fetch_latest_dependency_version("package[extra1,extra2]")

    mock_get.assert_called_once_with("https://pypi.org/pypi/package/json")
    assert version == "1.2.3"
