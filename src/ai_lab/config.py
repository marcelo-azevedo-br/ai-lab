from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import os
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
    runtime: str
    tools: tuple[str, ...]
    max_tool_rounds: int = 1


@dataclass(slots=True)
class RuntimeConfig:
    worker_runtime: str
    langgraph_enabled: bool
    tool_trace_enabled: bool


@dataclass(slots=True)
class BraveSearchConfig:
    enabled: bool
    endpoint: str
    api_key_env: str
    count: int
    country: str
    search_lang: str
    ui_lang: str
    min_interval_seconds: float
    retry_429_seconds: float


@dataclass(slots=True)
class FetchConfig:
    enabled: bool
    timeout_seconds: int
    max_chars: int
    max_pages: int
    user_agent: str


@dataclass(slots=True)
class RepoToolConfig:
    enabled: bool
    max_files: int
    max_matches: int


@dataclass(slots=True)
class BrowserToolConfig:
    specialist: str
    playwright_mcp_enabled: bool


@dataclass(slots=True)
class ToolsConfig:
    brave_search: BraveSearchConfig
    fetch: FetchConfig
    repo: RepoToolConfig
    browser: BrowserToolConfig


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
    runtime: RuntimeConfig
    tools: ToolsConfig
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


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def is_langgraph_installed() -> bool:
    return importlib.util.find_spec("langgraph") is not None


def load_config(config_path: str | Path = "config/factory.toml", *, root_dir: str | Path | None = None) -> FactoryConfig:
    root = Path(root_dir or Path.cwd()).resolve()
    config_file = (root / config_path).resolve()
    data = tomllib.loads(config_file.read_text(encoding="utf-8"))

    workspace_data = data["workspace"]
    orchestrator_data = data["orchestrator"]
    runtime_data = data["runtime"]
    tools_data = data["tools"]
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
        command=os.getenv("AI_LAB_CODEX_COMMAND", orchestrator_data["command"]),
        model=os.getenv("AI_LAB_CODEX_MODEL", orchestrator_data["model"]),
        sandbox=orchestrator_data["sandbox"],
        approval_policy=orchestrator_data["approval_policy"],
        full_auto=bool(orchestrator_data.get("full_auto", False)),
        role_file=_resolve(root, orchestrator_data["role_file"]),
    )
    runtime = RuntimeConfig(
        worker_runtime=os.getenv("AI_LAB_WORKER_RUNTIME", runtime_data["worker_runtime"]),
        langgraph_enabled=_env_bool("AI_LAB_LANGGRAPH_ENABLED", bool(runtime_data.get("langgraph_enabled", False))),
        tool_trace_enabled=_env_bool("AI_LAB_TOOL_TRACE_ENABLED", bool(runtime_data.get("tool_trace_enabled", True))),
    )
    tools = ToolsConfig(
        brave_search=BraveSearchConfig(
            enabled=bool(tools_data["brave_search"].get("enabled", True)),
            endpoint=tools_data["brave_search"]["endpoint"],
            api_key_env=tools_data["brave_search"]["api_key_env"],
            count=int(tools_data["brave_search"].get("count", 5)),
            country=tools_data["brave_search"].get("country", "BR"),
            search_lang=tools_data["brave_search"].get("search_lang", "pt"),
            ui_lang=tools_data["brave_search"].get("ui_lang", "pt-BR"),
            min_interval_seconds=float(tools_data["brave_search"].get("min_interval_seconds", 1.2)),
            retry_429_seconds=float(tools_data["brave_search"].get("retry_429_seconds", 2.0)),
        ),
        fetch=FetchConfig(
            enabled=bool(tools_data["fetch"].get("enabled", True)),
            timeout_seconds=int(tools_data["fetch"].get("timeout_seconds", 20)),
            max_chars=int(tools_data["fetch"].get("max_chars", 6000)),
            max_pages=int(tools_data["fetch"].get("max_pages", 3)),
            user_agent=tools_data["fetch"].get("user_agent", "ai-lab/0.2"),
        ),
        repo=RepoToolConfig(
            enabled=bool(tools_data["repo"].get("enabled", True)),
            max_files=int(tools_data["repo"].get("max_files", 200)),
            max_matches=int(tools_data["repo"].get("max_matches", 50)),
        ),
        browser=BrowserToolConfig(
            specialist=tools_data["browser"].get("specialist", "codex"),
            playwright_mcp_enabled=bool(tools_data["browser"].get("playwright_mcp_enabled", False)),
        ),
    )

    workers: dict[str, WorkerConfig] = {}
    for name, worker_data in workers_data.items():
        env_model = os.getenv(f"AI_LAB_{name.upper()}_MODEL")
        env_command = os.getenv(f"AI_LAB_{name.upper()}_COMMAND")
        workers[name] = WorkerConfig(
            name=name,
            provider=worker_data["provider"],
            command=env_command or worker_data["command"],
            model=env_model or worker_data["model"],
            role_file=_resolve(root, worker_data["role_file"]),
            runtime=worker_data.get("runtime", runtime.worker_runtime),
            tools=tuple(worker_data.get("tools", [])),
            max_tool_rounds=int(worker_data.get("max_tool_rounds", 1)),
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
        runtime=runtime,
        tools=tools,
        workers=workers,
        steps=steps,
    )
