import os
import sys
import unittest
from pathlib import Path

# tests/ の親 (= Plugins/TexNamingImporter/Content/Python) を import パスに追加
THIS_FILE = Path(__file__).resolve()
PYTHON_DIR = THIS_FILE.parents[1]
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

# 被テスト対象
from validator import validate_suffixes, ValidationResult, build_suffix_grid
from suffix_config import TextureSuffixConfig, load_texture_suffix_config


def _load_cfg_and_grid() -> tuple[TextureSuffixConfig, list[list[str]]]:
    """設定ファイルを読み込んで (cfg, suffix_grid) を返す。なければ明確なメッセージで失敗。"""

    cfg_path = Path(PYTHON_DIR, "tests", "assets","SuffixSettings.json")
    if not cfg_path.exists():
        raise FileNotFoundError(f"SuffixSettings.json が見つかりません: {cfg_path}")

    cfg = load_texture_suffix_config(cfg_path)
    grid = build_suffix_grid(cfg)
    return cfg, grid


class TestValidateSuffixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.suffix_grid = _load_cfg_and_grid()

    # -------- ヘルパ --------
    def _pick_valid_suffix_list(self) -> list[str]:
        """
        suffix_grid から、行ごとに最初の合法トークンを1つ選んで、
        現実的な OK 入力（大文字小文字混在させない素直な値）を作る。
        行が空ならテストをスキップ。
        """
        grid = self.suffix_grid
        if not grid:
            self.skipTest("suffix_grid が空のためテストをスキップします。")
        picked: list[str] = []
        for row, allowed in enumerate(grid):
            if not allowed:
                self.skipTest(f"suffix_grid の行 {row} が空のためテストをスキップします。")
            picked.append(str(allowed[0]))
        return picked

    # ---------- 成功ケース ----------

    def test_ok_basic(self):
        """設定から作った合法なサフィックス列は OK になる。"""
        suffix_list = self._pick_valid_suffix_list()
        res: ValidationResult = validate_suffixes(suffix_list, self.suffix_grid)
        self.assertTrue(res.ok, f"想定OKなのにNG: {res.error}")
        self.assertEqual(res.matches_by_row, suffix_list)

    def test_ok_case_insensitive(self):
        """大文字小文字無視でマッチすること（合法列を大文字化して検証）。"""
        suffix_list = [s.upper() for s in self._pick_valid_suffix_list()]
        res: ValidationResult = validate_suffixes(suffix_list, self.suffix_grid)
        self.assertTrue(res.ok, f"大小無視のはずがNG: {res.error}")
        self.assertEqual(res.matches_by_row, suffix_list)

    # ---------- 失敗ケース（※テスト結果は “想定どおりNGを検出できた” で成功） ----------

    def test_ng_length_mismatch_short(self):
        """行数(=カテゴリ数)より短い場合は NG を返す（= テストは成功）。"""
        valid = self._pick_valid_suffix_list()
        if len(valid) == 0:
            self.skipTest("suffix_grid が空です。")
        shorter = valid[:-1]  # 1つ減らす
        res: ValidationResult = validate_suffixes(shorter, self.suffix_grid)
        self.assertFalse(res.ok)
        self.assertIsNone(res.failed_row_index)  # 実装では長さ不一致は None
        self.assertIn("一致しません", res.error or "")
        print(res.error)


    def test_ng_length_mismatch_long(self):
        """行数(=カテゴリ数)より長い場合も NG を返す（= テストは成功）。"""
        valid = self._pick_valid_suffix_list()
        longer = valid + ["__extra__"]
        res: ValidationResult = validate_suffixes(longer, self.suffix_grid)
        self.assertFalse(res.ok)
        self.assertIsNone(res.failed_row_index)
        self.assertIn("一致しません", res.error or "")
        print(res.error)

    def test_ng_invalid_first_row(self):
        """先頭行のトークンを不正値にして NG を返す（= テストは成功）。"""
        valid = self._pick_valid_suffix_list()
        invalid = list(valid)
        invalid[0] = "__invalid__"
        res: ValidationResult = validate_suffixes(invalid, self.suffix_grid)
        self.assertFalse(res.ok)
        self.assertEqual(res.failed_row_index, 0)
        self.assertIn("許容値", res.error or "")
        print(res.error)

    def test_ng_invalid_last_row(self):
        """
        最終行のトークンを不正値にして NG を返す（= テストは成功）。
        行数が1未満ならスキップ。
        """
        valid = self._pick_valid_suffix_list()
        if len(valid) < 2:
            self.skipTest("行数が1行のみの設定のため、このNGケースはスキップします。")
        invalid = list(valid)
        last = len(invalid) - 1
        invalid[last] = "__invalid__"
        res: ValidationResult = validate_suffixes(invalid, self.suffix_grid)
        self.assertFalse(res.ok)
        self.assertEqual(res.failed_row_index, last)
        self.assertIn("許容値", res.error or "")
        print(res.error)


if __name__ == "__main__":
    # 実行例（Python ディレクトリ直下で）:
    #   python -m unittest tests/test_validator.py -v
    unittest.main(verbosity=2)