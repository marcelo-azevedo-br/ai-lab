from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(slots=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


class CommandError(RuntimeError):
    def __init__(self, result: CommandResult):
        super().__init__(self._build_message(result))
        self.result = result

    @staticmethod
    def _build_message(result: CommandResult) -> str:
        return (
            f"Command failed with exit code {result.returncode}: {' '.join(result.command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )


class ShellRunner:
    def run(
        self,
        command: list[str],
        *,
        cwd: Path,
        input_text: str | None = None,
        timeout: int = 600,
        allow_failure: bool = False,
    ) -> CommandResult:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            input=input_text,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        result = CommandResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
        if result.returncode != 0 and not allow_failure:
            raise CommandError(result)
        return result
