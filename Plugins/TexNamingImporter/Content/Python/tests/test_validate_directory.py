import sys
import unittest
from pathlib import Path

# tests/ の親 (= Plugins/TexNamingImporter/Content/Python) を import パスに追加
THIS_FILE = Path(__file__).resolve()
PYTHON_DIR = THIS_FILE.parents[1]
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from validator import validate_directory  # noqa: E402


class TestValidateDirectory(unittest.TestCase):
    def setUp(self):
        # 許容ディレクトリの基本セット
        self.allowed = ["/Game/VFX", "/Game/Characters"]

    def test_true_cases_basic_and_subdirs(self):
        true_cases = [
            "/Game/VFX/Smoke/T_Smoke.T_Smoke",       # サブディレクトリ配下
            "/Game/Characters/Hero/T_Hero.T_Hero",   # 別の許容ディレクトリ配下
            "/Game/VFX/T_Fire.T_Fire",               # 直下
            "/Game/VFX/Smoke/",                      # ディレクトリで与えてもOK
            "/Game/VFX/Smoke/T_Smoke",               # 拡張子/オブジェクト名なし
            r"\Game\VFX\Smoke\T_Smoke.T_Smoke",      # バックスラッシュ
        ]
        for p in true_cases:
            with self.subTest(p=p):
                self.assertTrue(
                    validate_directory(p, self.allowed),
                    f"True になるべき: {p}",
                )

    def test_true_with_allowed_trailing_slash(self):
        # 許容ディレクトリに末尾スラッシュがあっても True
        allowed = ["/Game/VFX/", "/Game/Characters/"]
        p = "/Game/VFX/Smoke/T_Smoke.T_Smoke"
        self.assertTrue(validate_directory(p, allowed))

    def test_false_cases_outside_or_boundary(self):
        false_cases = [
            "/Game/Env/Trees/T_Tree.T_Tree",   # 許容外
            "/Game/VFXFoo/FX/T_X.T_X",         # 境界（VFXFoo は VFX の配下ではない）
            "/Game/VF/T_X.T_X",                # 似ているが別
            "",                                 # 空
            None,                               # None
            "T_Smoke.T_Smoke",                 # ルート不明
            "/Game",                            # 直ルート（ディレクトリ抽出で '/' → 許容外）
        ]
        for p in false_cases:
            with self.subTest(p=p):
                self.assertFalse(
                    validate_directory(p, self.allowed),
                    f"False になるべき: {p}",
                )

    def test_same_directory_exact_match(self):
        # 同一ディレクトリを与えた場合も True
        p = "/Game/VFX/T_Something.T_Something"
        allowed = ["/Game/VFX"]
        self.assertTrue(validate_directory(p, allowed))

if __name__ == "__main__":
    # 実行例（Python ディレクトリ直下で）:
    #   python -m unittest tests/test_validate_directory.py -v
    unittest.main(verbosity=2)