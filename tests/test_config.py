import unittest
from pathlib import Path
import sys
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ai_lab.config import load_config


class ConfigTests(unittest.TestCase):
    def test_load_config(self) -> None:
        config = load_config(root_dir=ROOT)

        self.assertEqual(config.workspace.name, "ai-lab")
        self.assertIn("research", config.workers)
        self.assertEqual(config.steps[0].name, "scan")

    def test_env_overrides_models(self) -> None:
        with mock.patch.dict(
            "os.environ",
            {
                "AI_LAB_CODEX_MODEL": "gpt-5-mini",
                "AI_LAB_DEV_MODEL": "qwen2.5-coder:7b",
            },
            clear=False,
        ):
            config = load_config(root_dir=ROOT)

        self.assertEqual(config.orchestrator.model, "gpt-5-mini")
        self.assertEqual(config.workers["dev"].model, "qwen2.5-coder:7b")


if __name__ == "__main__":
    unittest.main()
