from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(slots=True)
class WorkspaceConfig:
    root_dir: Path
    name: str
    runs_dir: Path
    products_dir: Path
    prompts_dir: Path
    agents_dir: Path


@dataclass(slots=True)
class OrchestratorConfig:
    provider: str
    command: str
    model: str
    sandbox: str
    approval_policy: str
    full_auto: bool
    role_file: Path


@dataclass(slots=True)
class WorkerConfig:
    name: str
    provider: str
    command: str
    model: str
    role_file: Path


@dataclass(slots=True)
class StepConfig:
    name: str
    executor: str
    prompt: str
    output: str
    gate: str


@dataclass(slots=True)
class FactoryConfig:
    workspace: WorkspaceConfig
    orchestrator: OrchestratorConfig
    workers: dict[str, WorkerConfig]
    steps: list[StepConfig]

    def step_names(self) -> list[str]:
        return [step.name for step in self.steps]

    def gates(self) -> list[str]:
        seen: list[str] = []
        for step in self.steps:
            if step.gate and step.gate not in seen:
                seen.append(step.gate)
        return seen


def _resolve(root_dir: Path, value: str) -> Path:
    return (root_dir / value).resolve()


def load_config(config_path: str | Path = "config/factory.toml", *, root_dir: str | Path | None = None) -> FactoryConfig:
    root = Path(root_dir or Path.cwd()).resolve()
    config_file = (root / config_path).resolve()
    data = tomllib.loads(config_file.read_text(encoding="utf-8"))

    workspace_data = data["workspace"]
    orchestrator_data = data["orchestrator"]
    workers_data = data["workers"]
    steps_data = data["pipeline"]["steps"]

    workspace = WorkspaceConfig(
        root_dir=root,
        name=workspace_data["name"],
        runs_dir=_resolve(root, workspace_data["runs_dir"]),
        products_dir=_resolve(root, workspace_data["products_dir"]),
        prompts_dir=_resolve(root, workspace_data["prompts_dir"]),
        agents_dir=_resolve(root, workspace_data["agents_dir"]),
    )
    orchestrator = OrchestratorConfig(
        provider=orchestrator_data["provider"],
        command=orchestrator_data["command"],
        model=orchestrator_data["model"],
        sandbox=orchestrator_data["sandbox"],
        approval_policy=orchestrator_data["approval_policy"],
        full_auto=bool(orchestrator_data.get("full_auto", False)),
        role_file=_resolve(root, orchestrator_data["role_file"]),
    )

    workers: dict[str, WorkerConfig] = {}
    for name, worker_data in workers_data.items():
        workers[name] = WorkerConfig(
            name=name,
            provider=worker_data["provider"],
            command=worker_data["command"],
            model=worker_data["model"],
            role_file=_resolve(root, worker_data["role_file"]),
        )

    steps = [
        StepConfig(
            name=step["name"],
            executor=step["executor"],
            prompt=step["prompt"],
            output=step["output"],
            gate=step["gate"],
        )
        for step in steps_data
    ]

    return FactoryConfig(
        workspace=workspace,
        orchestrator=orchestrator,
        workers=workers,
        steps=steps,
    )
