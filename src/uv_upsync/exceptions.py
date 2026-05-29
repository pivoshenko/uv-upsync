"""Module that contains implementation of the exceptions."""

from __future__ import annotations


class BaseError(Exception):
    """Base class for all uv-upsync errors."""


class UVCommandError(BaseError):
    def __init__(self, command: list[str], returncode: int, stdout: str, stderr: str) -> None:
        message = f"Command {command!r} returned non-zero exit status {returncode}"
        if stdout:
            message += f"\n\nStdout:\n{stdout}"
        if stderr:
            message += f"\n\nStderr:\n{stderr}"
        super().__init__(message)
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
