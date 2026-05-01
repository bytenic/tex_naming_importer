import json
import sys
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PYTHON_DIR = THIS_FILE.parents[1]
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

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

    def test_ignore_import_suffix_defaults_to_none(self):
        """Missing ignore_import_suffix should be represented as None."""
        cfg = Config.load(self.asset_path)
        self.assertIsNone(cfg.ignore_import_suffix)

    def test_ignore_import_suffix_loads_string_value(self):
        """ignore_import_suffix should load from JSON when explicitly configured."""
        data = json.loads(self.asset_path.read_text(encoding="utf-8"))
        data["ignore_import_suffix"] = "manual"

        cfg = Config.from_dict(data)

        self.assertEqual(cfg.ignore_import_suffix, "manual")
        self.assertEqual(cfg.to_dict()["ignore_import_suffix"], "manual")


if __name__ == "__main__":
    unittest.main(verbosity=2)
