from __future__ import annotations

from pathlib import Path
from string import Template

from ai_lab.models import RunManifest


class PromptRenderer:
    def __init__(self, prompts_dir: Path) -> None:
        self.prompts_dir = prompts_dir

    def render(
        self,
        prompt_name: str,
        *,
        manifest: RunManifest,
        context: str,
        previous_output: str,
        previous_tool_output: str = "",
    ) -> str:
        template = Template((self.prompts_dir / prompt_name).read_text(encoding="utf-8"))
        payload = {
            "vertical": manifest.vertical,
            "objective": manifest.objective,
            "context": context,
            "previous_output": previous_output,
            "previous_tool_output": previous_tool_output,
            "approved_idea": manifest.approvals.get("idea", ""),
        }
        return template.safe_substitute(payload).strip() + "\n"
