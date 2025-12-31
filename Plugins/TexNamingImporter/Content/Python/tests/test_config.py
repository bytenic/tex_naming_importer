import json
import unittest
from pathlib import Path

from config import Config


class TestConfig(unittest.TestCase):
    """Unit tests for Content/Python/config.py"""

    @classmethod
    def setUpClass(cls):
        # Content/Python/tests/assets/Config.json
        cls.asset_path = Path(__file__).resolve().parent / "assets" / "Config.json"
        if not cls.asset_path.exists():
            raise FileNotFoundError(f"Missing test asset: {cls.asset_path}")

    def test_load_success(self):
        """Config.load() should succeed for the reference JSON."""
        cfg = Config.load(self.asset_path)
        self.assertIsInstance(cfg, Config)

    def test_loaded_content_matches_json(self):
        """Loaded Config should reflect the JSON content (round-trip via to_dict())."""
        expected = json.loads(self.asset_path.read_text(encoding="utf-8"))
        cfg = Config.load(self.asset_path)
        actual = cfg.to_dict()
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main(verbosity=2)
