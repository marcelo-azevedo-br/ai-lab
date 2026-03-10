from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class StepState:
    name: str
    executor: str
    status: str = "pending"
    prompt_file: str = ""
    output_file: str = ""
    started_at: str = ""
    completed_at: str = ""


@dataclass(slots=True)
class RunManifest:
    run_id: str
    vertical: str
    objective: str
    context: str
    product_slug: str
    product_dir: str
    created_at: str
    updated_at: str
    status: str = "created"
    gates: dict[str, bool] = field(default_factory=dict)
    approvals: dict[str, str] = field(default_factory=dict)
    steps: dict[str, StepState] = field(default_factory=dict)
    last_step: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["steps"] = {name: asdict(step) for name, step in self.steps.items()}
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunManifest":
        steps = {
            name: StepState(**step_data)
            for name, step_data in data.get("steps", {}).items()
        }
        return cls(
            run_id=data["run_id"],
            vertical=data["vertical"],
            objective=data["objective"],
            context=data.get("context", ""),
            product_slug=data["product_slug"],
            product_dir=data["product_dir"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            status=data.get("status", "created"),
            gates=dict(data.get("gates", {})),
            approvals=dict(data.get("approvals", {})),
            steps=steps,
            last_step=data.get("last_step", ""),
        )

    def run_dir(self, runs_dir: Path) -> Path:
        return runs_dir / self.run_id
