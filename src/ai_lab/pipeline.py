from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_lab.config import FactoryConfig, StepConfig
from ai_lab.models import RunManifest, StepState
from ai_lab.prompts import PromptRenderer
from ai_lab.providers import CodexProvider, ProviderResult, build_worker_provider
from ai_lab.run_store import RunStore
from ai_lab.shell import ShellRunner
from ai_lab.tooling import ToolRegistry
from ai_lab.utils import utc_now


@dataclass(slots=True)
class PipelineResult:
    run_id: str
    executed_steps: list[str]
    stopped_at_gate: str = ""
    status: str = "completed"


class PipelineRunner:
    def __init__(self, config: FactoryConfig, store: RunStore, shell_runner: ShellRunner | None = None) -> None:
        self.config = config
        self.store = store
        self.shell_runner = shell_runner or ShellRunner()
        self.prompt_renderer = PromptRenderer(config.workspace.prompts_dir)
        self.orchestrator = CodexProvider(config, self.shell_runner)
        self.tool_registry = ToolRegistry(config, self.shell_runner)
        self.workers = {
            name: build_worker_provider(worker, config, self.shell_runner, self.tool_registry)
            for name, worker in config.workers.items()
        }

    def run(self, run_id: str, *, through: str | None = None, force: bool = False, dry_run: bool = False) -> PipelineResult:
        manifest = self.store.load(run_id)
        executed_steps: list[str] = []
        previous_output = ""
        previous_tool_output = ""

        for step in self.config.steps:
            step_state = manifest.steps.get(step.name)
            if step_state and step_state.status == "completed":
                if not force:
                    previous_output = self._read_output(manifest, step)
                    previous_tool_output = self._read_tool_output(manifest, step_state)
                if step.gate and not manifest.gates.get(step.gate, False) and not force:
                    manifest.status = "waiting_approval"
                    self.store.save(manifest)
                    self.store.write_report(manifest)
                    return PipelineResult(
                        run_id=run_id,
                        executed_steps=executed_steps,
                        stopped_at_gate=step.gate,
                        status=manifest.status,
                    )
                if not force:
                    if through and step.name == through:
                        return PipelineResult(run_id=run_id, executed_steps=executed_steps, status=manifest.status)
                    continue

            result = self._execute_step(
                manifest,
                step,
                previous_output=previous_output,
                previous_tool_output=previous_tool_output,
                dry_run=dry_run,
            )
            executed_steps.append(step.name)
            previous_output = result.content
            previous_tool_output = self._read_tool_output(manifest, manifest.steps[step.name])
            if step.gate and not manifest.gates.get(step.gate, False):
                manifest.status = "waiting_approval"
                self.store.save(manifest)
                self.store.write_report(manifest)
                return PipelineResult(
                    run_id=run_id,
                    executed_steps=executed_steps,
                    stopped_at_gate=step.gate,
                    status=manifest.status,
                )
            if through and step.name == through:
                manifest.status = "paused"
                self.store.save(manifest)
                self.store.write_report(manifest)
                return PipelineResult(run_id=run_id, executed_steps=executed_steps, status=manifest.status)

        manifest.status = "completed"
        self.store.save(manifest)
        self.store.write_report(manifest)
        return PipelineResult(run_id=run_id, executed_steps=executed_steps, status=manifest.status)

    def _execute_step(
        self,
        manifest: RunManifest,
        step: StepConfig,
        *,
        previous_output: str,
        previous_tool_output: str,
        dry_run: bool,
    ) -> ProviderResult:
        run_dir = manifest.run_dir(self.config.workspace.runs_dir)
        prompt_path = run_dir / f"{step.name}.prompt.md"
        output_path = run_dir / step.output

        prompt = self.prompt_renderer.render(
            step.prompt,
            manifest=manifest,
            context=manifest.context,
            previous_output=previous_output,
            previous_tool_output=previous_tool_output,
        )
        prompt_path.write_text(prompt, encoding="utf-8")

        state = manifest.steps.get(step.name, StepState(name=step.name, executor=step.executor))
        state.status = "running"
        state.prompt_file = prompt_path.name
        state.output_file = output_path.name
        state.started_at = utc_now()
        manifest.steps[step.name] = state
        manifest.status = "running"
        self.store.save(manifest)

        if dry_run:
            content = f"[dry-run] {step.name}\n"
            output_path.write_text(content, encoding="utf-8")
            result = ProviderResult(content=content, command=["dry-run"], stdout=content, stderr="")
        else:
            provider = self.orchestrator if step.executor == "orchestrator" else self.workers[step.executor]
            result = provider.execute(prompt, cwd=self.config.workspace.root_dir, output_file=output_path)
            if not output_path.exists():
                output_path.write_text(result.content + "\n", encoding="utf-8")

        state.status = "completed"
        state.completed_at = utc_now()
        state.tool_report_file = Path(result.artifacts.get("tool_report", "")).name if result.artifacts.get("tool_report") else ""
        manifest.steps[step.name] = state
        manifest.last_step = step.name
        self.store.save(manifest)
        self.store.write_report(manifest)
        return result

    def _read_output(self, manifest: RunManifest, step: StepConfig) -> str:
        run_dir = manifest.run_dir(self.config.workspace.runs_dir)
        output_path = run_dir / step.output
        if output_path.exists():
            return output_path.read_text(encoding="utf-8")
        return ""

    def _read_tool_output(self, manifest: RunManifest, step_state: StepState | None) -> str:
        if not step_state or not step_state.tool_report_file:
            return ""
        run_dir = manifest.run_dir(self.config.workspace.runs_dir)
        tool_path = run_dir / step_state.tool_report_file
        if tool_path.exists():
            return tool_path.read_text(encoding="utf-8")
        return ""
