from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ai_lab.config import FactoryConfig, WorkerConfig
from ai_lab.shell import ShellRunner
from ai_lab.tooling import ToolRegistry


@dataclass(slots=True)
class ProviderResult:
    content: str
    command: list[str]
    stdout: str
    stderr: str
    artifacts: dict[str, str] = field(default_factory=dict)


class BaseProvider:
    def __init__(self, command: str, model: str, role_file: Path, shell_runner: ShellRunner) -> None:
        self.command = command
        self.model = model
        self.role_file = role_file
        self.shell_runner = shell_runner

    def build_prompt(self, prompt: str) -> str:
        role = self.role_file.read_text(encoding="utf-8").strip()
        return f"{role}\n\n{prompt}".strip()


class CodexProvider(BaseProvider):
    def __init__(self, config: FactoryConfig, shell_runner: ShellRunner) -> None:
        super().__init__(
            config.orchestrator.command,
            config.orchestrator.model,
            config.orchestrator.role_file,
            shell_runner,
        )
        self.config = config

    def execute(self, prompt: str, *, cwd: Path, output_file: Path) -> ProviderResult:
        final_prompt = self.build_prompt(prompt)
        command = [
            self.command,
            "exec",
            "-C",
            str(cwd),
            "-m",
            self.model,
            "-o",
            str(output_file),
            "-s",
            self.config.orchestrator.sandbox,
            "--skip-git-repo-check",
        ]
        if self.config.orchestrator.full_auto:
            command.append("--full-auto")
        command.append("-")

        result = self.shell_runner.run(command, cwd=cwd, input_text=final_prompt)
        content = output_file.read_text(encoding="utf-8") if output_file.exists() else result.stdout
        return ProviderResult(
            content=content.strip(),
            command=command,
            stdout=result.stdout,
            stderr=result.stderr,
        )


class OllamaProvider(BaseProvider):
    def __init__(self, worker: WorkerConfig, config: FactoryConfig, shell_runner: ShellRunner, tool_registry: ToolRegistry) -> None:
        super().__init__(worker.command, worker.model, worker.role_file, shell_runner)
        self.worker = worker
        self.config = config
        self.tool_registry = tool_registry

    def execute(self, prompt: str, *, cwd: Path, output_file: Path) -> ProviderResult:
        tool_report = ""
        artifacts: dict[str, str] = {}
        if self.worker.runtime == "tool-agent":
            tool_report, _ = self.tool_registry.build_report(self.worker, prompt, cwd=cwd)
            tool_report_path = output_file.with_suffix(".tools.md")
            tool_report_path.write_text(tool_report, encoding="utf-8")
            artifacts["tool_report"] = str(tool_report_path)
        final_prompt = self.build_prompt(prompt)
        if tool_report:
            final_prompt = (
                f"{final_prompt}\n\n"
                "Use as evidencias reais abaixo como contexto prioritario. "
                "Se houver conflito entre memoria do modelo e os artifacts de tool, priorize os artifacts.\n\n"
                f"{tool_report}"
            )
        command = [self.command, "run", self.model, final_prompt]
        result = self.shell_runner.run(command, cwd=cwd)
        content = result.stdout.strip()
        output_file.write_text(content + "\n", encoding="utf-8")
        return ProviderResult(
            content=content,
            command=command,
            stdout=result.stdout,
            stderr=result.stderr,
            artifacts=artifacts,
        )


def build_worker_provider(worker: WorkerConfig, config: FactoryConfig, shell_runner: ShellRunner, tool_registry: ToolRegistry) -> BaseProvider:
    if worker.provider != "ollama":
        raise ValueError(f"Unsupported worker provider: {worker.provider}")
    return OllamaProvider(worker, config, shell_runner, tool_registry)
