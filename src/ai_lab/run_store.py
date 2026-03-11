from __future__ import annotations

from pathlib import Path
import json

from ai_lab.config import FactoryConfig
from ai_lab.models import RunManifest
from ai_lab.utils import compact_timestamp, slugify, utc_now


class RunStore:
    def __init__(self, config: FactoryConfig) -> None:
        self.config = config
        self.config.workspace.runs_dir.mkdir(parents=True, exist_ok=True)
        self.config.workspace.products_dir.mkdir(parents=True, exist_ok=True)

    def create_run(self, *, vertical: str, objective: str, context: str = "") -> RunManifest:
        run_id = f"run-{compact_timestamp()}-{slugify(vertical)}"
        product_slug = slugify(vertical)
        product_dir = self.config.workspace.products_dir / product_slug
        product_dir.mkdir(parents=True, exist_ok=True)
        manifest = RunManifest(
            run_id=run_id,
            vertical=vertical,
            objective=objective,
            context=context,
            product_slug=product_slug,
            product_dir=str(product_dir),
            created_at=utc_now(),
            updated_at=utc_now(),
            status="created",
            gates={gate: False for gate in self.config.gates()},
        )
        run_dir = manifest.run_dir(self.config.workspace.runs_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        (Path(manifest.product_dir) / "README.md").write_text(
            f"# {vertical}\n\nRun inicial: `{run_id}`\n\nObjetivo: {objective}\n",
            encoding="utf-8",
        )
        self.save(manifest)
        self.write_report(manifest)
        return manifest

    def manifest_path(self, run_id: str) -> Path:
        return self.config.workspace.runs_dir / run_id / "run.json"

    def load(self, run_id: str) -> RunManifest:
        path = self.manifest_path(run_id)
        data = json.loads(path.read_text(encoding="utf-8"))
        return RunManifest.from_dict(data)

    def save(self, manifest: RunManifest) -> None:
        manifest.updated_at = utc_now()
        path = self.manifest_path(manifest.run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(manifest.to_dict(), indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

    def approve(self, manifest: RunManifest, gate: str, note: str = "") -> RunManifest:
        if gate not in manifest.gates:
            raise ValueError(f"Unknown gate: {gate}")
        manifest.gates[gate] = True
        if note:
            manifest.approvals[gate] = note
        manifest.status = "approved"
        self.save(manifest)
        self.write_report(manifest)
        return manifest

    def write_report(self, manifest: RunManifest) -> Path:
        run_dir = manifest.run_dir(self.config.workspace.runs_dir)
        report_path = run_dir / "run-report.md"
        lines = [
            f"# {manifest.run_id}",
            "",
            f"- vertical: {manifest.vertical}",
            f"- objetivo: {manifest.objective}",
            f"- status: {manifest.status}",
            f"- produto: {manifest.product_dir}",
            f"- criado em: {manifest.created_at}",
            f"- atualizado em: {manifest.updated_at}",
            "",
            "## Gates",
            "",
        ]
        for gate, approved in manifest.gates.items():
            note = manifest.approvals.get(gate, "")
            status = "approved" if approved else "pending"
            suffix = f" | nota: {note}" if note else ""
            lines.append(f"- {gate}: {status}{suffix}")

        lines.extend(["", "## Steps", ""])
        if not manifest.steps:
            lines.append("- nenhum step executado ainda")
        else:
            for step in manifest.steps.values():
                tool_suffix = f" | tools: {step.tool_report_file}" if step.tool_report_file else ""
                lines.append(
                    f"- {step.name}: {step.status} | executor: {step.executor} | output: {step.output_file or '-'}{tool_suffix}"
                )

        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return report_path
