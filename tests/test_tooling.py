import tempfile
import unittest
from pathlib import Path
import sys
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ai_lab.config import load_config
from ai_lab.shell import ShellRunner
from ai_lab.tooling import ToolRegistry


class ToolingTests(unittest.TestCase):
    def test_research_report_skips_brave_without_key(self) -> None:
        config = load_config(root_dir=ROOT)
        registry = ToolRegistry(config, ShellRunner())

        with mock.patch.dict("os.environ", {}, clear=False):
            report, events = registry.build_report(
                config.workers["research"],
                "Vertical: guincho\nObjetivo: Automacao via WhatsApp\n",
                cwd=ROOT,
            )

        self.assertIn("missing env BRAVE_SEARCH_API_KEY", report)
        self.assertEqual(events[0].name, "brave_search")
        self.assertEqual(events[0].status, "skipped")

    def test_dev_report_uses_repo_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("guincho build marketing\n", encoding="utf-8")
            (root / "notes.txt").write_text("landing whatsapp\n", encoding="utf-8")

            config = load_config(root_dir=ROOT)
            registry = ToolRegistry(config, ShellRunner())
            report, events = registry.build_report(
                config.workers["dev"],
                "Vertical: guincho\nObjective: build MVP landing\n",
                cwd=root,
            )

        event_names = [event.name for event in events]
        self.assertIn("repo_snapshot", event_names)
        self.assertIn("repo_search", event_names)
        self.assertIn("git_status", event_names)
        self.assertIn("README.md", report)


if __name__ == "__main__":
    unittest.main()
