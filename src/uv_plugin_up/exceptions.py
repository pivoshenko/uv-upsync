"""Module that contains implementation of the exceptions."""

from __future__ import annotations


class BaseError(Exception):
    pass


class InvalidDependencySpecifierError(BaseError):
    def __init__(self, dependency_specifier: str) -> None:
        super().__init__(f"Invalid dependency specifier: {dependency_specifier!r}")


class NoOperatorFoundError(BaseError):
    def __init__(self, dependency_specifier: str) -> None:
        super().__init__(f"No operator found in dependency specifier: {dependency_specifier!r}")


class MultipleOperatorsFoundError(BaseError):
    def __init__(self, dependency_specifier: str) -> None:
        super().__init__(
            f"Multiple operators found in dependency specifier: {dependency_specifier!r}",
        )


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
