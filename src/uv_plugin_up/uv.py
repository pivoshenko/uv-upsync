"""Module that contains implementation of the uv commands."""

from __future__ import annotations

import subprocess

from uv_plugin_up import exceptions


def lock() -> None:
    try:
        subprocess.run(
            ("uv", "lock"),
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exception:
        raise exceptions.UVCommandError(
            command=exception.cmd,
            returncode=exception.returncode,
            stdout=exception.stdout,
            stderr=exception.stderr,
        ) from exception
