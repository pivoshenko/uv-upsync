"""Module that contains a thin wrapper around the `uv` CLI."""

from __future__ import annotations

import subprocess

from typing import TYPE_CHECKING

from uv_upsync import exceptions


if TYPE_CHECKING:
    import pathlib


def lock(*, offline: bool = False, cwd: pathlib.Path | None = None) -> None:
    command = ["uv", "lock"]
    if offline:
        command.append("--offline")

    try:
        subprocess.run(  # noqa: S603
            command,
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd,
        )
    except subprocess.CalledProcessError as exception:
        raise exceptions.UVCommandError(
            command=exception.cmd,
            returncode=exception.returncode,
            stdout=exception.stdout,
            stderr=exception.stderr,
        ) from exception
