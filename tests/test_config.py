import unittest
from pathlib import Path
import sys

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


if __name__ == "__main__":
    unittest.main()
