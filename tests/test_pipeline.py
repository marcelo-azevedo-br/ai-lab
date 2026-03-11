import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ai_lab.config import load_config
from ai_lab.pipeline import PipelineRunner
from ai_lab.providers import ProviderResult
from ai_lab.run_store import RunStore
from ai_lab.shell import ShellRunner


class FakeProvider:
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls = 0

    def execute(self, prompt: str, *, cwd: Path, output_file: Path) -> ProviderResult:
        self.calls += 1
        content = f"{self.name}:{output_file.name}"
        output_file.write_text(content + "\n", encoding="utf-8")
        return ProviderResult(content=content, command=[self.name], stdout=content, stderr="")


class PipelineTests(unittest.TestCase):
    def test_run_stops_on_first_pending_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in ["config", "factory", "products"]:
                self._copy_tree(ROOT / relative, root / relative)

            config = load_config(root_dir=root)
            store = RunStore(config)
            manifest = store.create_run(vertical="guincho", objective="Automatizar atendimento")
            runner = PipelineRunner(config, store, shell_runner=ShellRunner())
            runner.orchestrator = FakeProvider("codex")
            runner.workers = {
                "research": FakeProvider("research"),
                "analyst": FakeProvider("analyst"),
                "dev": FakeProvider("dev"),
                "marketing": FakeProvider("marketing"),
            }

            result = runner.run(manifest.run_id)

            self.assertEqual(result.executed_steps, ["scan", "score"])
            self.assertEqual(result.stopped_at_gate, "idea")
            updated = store.load(manifest.run_id)
            self.assertEqual(updated.status, "waiting_approval")

    def test_run_can_continue_after_approvals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in ["config", "factory", "products"]:
                self._copy_tree(ROOT / relative, root / relative)

            config = load_config(root_dir=root)
            store = RunStore(config)
            manifest = store.create_run(vertical="pilates", objective="Automatizar agenda")
            runner = PipelineRunner(config, store, shell_runner=ShellRunner())
            runner.orchestrator = FakeProvider("codex")
            runner.workers = {
                "research": FakeProvider("research"),
                "analyst": FakeProvider("analyst"),
                "dev": FakeProvider("dev"),
                "marketing": FakeProvider("marketing"),
            }

            first = runner.run(manifest.run_id)
            self.assertEqual(first.stopped_at_gate, "idea")

            store.approve(store.load(manifest.run_id), "idea", "Automacao para empresas de pilates")
            second = runner.run(manifest.run_id)
            self.assertEqual(second.executed_steps, ["spec"])
            self.assertEqual(second.stopped_at_gate, "mvp")

            store.approve(store.load(manifest.run_id), "mvp", "MVP aprovado")
            third = runner.run(manifest.run_id)
            self.assertEqual(third.executed_steps, ["build"])
            self.assertEqual(third.stopped_at_gate, "build")

            store.approve(store.load(manifest.run_id), "build", "Build aprovado")
            fourth = runner.run(manifest.run_id)
            self.assertEqual(fourth.executed_steps, ["marketing"])
            self.assertEqual(fourth.status, "completed")

    def test_force_reruns_completed_step_before_pending_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in ["config", "factory", "products"]:
                self._copy_tree(ROOT / relative, root / relative)

            config = load_config(root_dir=root)
            store = RunStore(config)
            manifest = store.create_run(vertical="guincho", objective="Automatizar atendimento")
            runner = PipelineRunner(config, store, shell_runner=ShellRunner())
            research = FakeProvider("research")
            orchestrator = FakeProvider("codex")
            runner.orchestrator = orchestrator
            runner.workers = {
                "research": research,
                "analyst": FakeProvider("analyst"),
                "dev": FakeProvider("dev"),
                "marketing": FakeProvider("marketing"),
            }

            first = runner.run(manifest.run_id)
            self.assertEqual(first.executed_steps, ["scan", "score"])
            self.assertEqual(first.stopped_at_gate, "idea")
            self.assertEqual(research.calls, 1)
            self.assertEqual(orchestrator.calls, 1)

            second = runner.run(manifest.run_id, through="score", force=True)
            self.assertEqual(second.executed_steps, ["scan", "score"])
            self.assertEqual(second.stopped_at_gate, "idea")
            self.assertEqual(research.calls, 2)
            self.assertEqual(orchestrator.calls, 2)

    def _copy_tree(self, source: Path, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)
        for path in source.rglob("*"):
            relative = path.relative_to(source)
            destination = target / relative
            if path.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
