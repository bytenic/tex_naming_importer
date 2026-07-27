import json
import sys
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PYTHON_DIR = THIS_FILE.parents[1]
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from config import (
    Config,
    TextureConfigParams,
    override_address_uv,
    override_subuv_max_in_game,
)
from type_define import AddressMode


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

    def test_subuv_override_does_not_mutate_shared_base_settings(self):
        """SubUV override must not leak into the following non-SubUV texture."""
        base_settings = TextureConfigParams(
            address_u=AddressMode.WRAP,
            address_v=AddressMode.WRAP,
            max_in_game=4096,
        )

        subuv_settings = override_subuv_max_in_game(
            override_address_uv(base_settings, AddressMode.CLAMP, AddressMode.CLAMP),
            2048,
        )

        self.assertEqual(subuv_settings.max_in_game, 2048)
        self.assertEqual(subuv_settings.address_u, AddressMode.CLAMP)
        self.assertEqual(subuv_settings.address_v, AddressMode.CLAMP)

        # texture_config 内で共有される元設定は、次の通常テクスチャにも使われる。
        self.assertEqual(base_settings.max_in_game, 4096)
        self.assertEqual(base_settings.address_u, AddressMode.WRAP)
        self.assertEqual(base_settings.address_v, AddressMode.WRAP)


if __name__ == "__main__":
    unittest.main(verbosity=2)
