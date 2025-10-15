import unittest
import sys
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PYTHON_DIR = THIS_FILE.parents[1]
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from path_utils.path_functions import collect_suffixes_from_path

SUFFIX_ARRAY = ["cc","cw","cm","wc","ww","wm","mc","mw","mm","col","msk","nml","mat","cub","flw"]

class TestCollectSuffixesFromPath(unittest.TestCase):
    def test_three_suffixes_found(self):
        # 末尾から3連続のサフィックスが見つかるケース
        cases = [
            ("/home/dev/proj/textures/CharA/FaceDiff_cc_msk_nml.png", ['cc', 'msk', 'nml']),
            ("/home/dev/assets/P0_P1_Tree_mat_col_nml.tga",           ['mat', 'col', 'nml']),
            ("/srv/game/tiles/Tileset_v2_cub_cc_flw.exr",             ['cub', 'cc', 'flw']),
        ]
        for path, expected in cases:
            with self.subTest(path=path):
                suffix, tokens = collect_suffixes_from_path(path, SUFFIX_ARRAY)
                self.assertEqual(suffix, expected)

    def test_two_suffixes_found(self):
        # 末尾から2連続のサフィックスが見つかるケース
        cases = [
            ("/home/dev/work/tex/Rock_nml_msk.png",  ['nml', 'msk']),
            ("/home/dev/tex/Skybox_ww_wm.jpg",       ['ww', 'wm']),
            ("/var/data/maps/FloorTile_mw_cc.tif",   ['mw', 'cc']),
        ]
        for path, expected in cases:
            with self.subTest(path=path):
                suffix, tokens = collect_suffixes_from_path(path, SUFFIX_ARRAY)
                self.assertEqual(suffix, expected)

    def test_ending_not_suffix(self):
        # 末尾トークンがサフィックスではないため打ち切り（空配列）
        cases = [
            ("/home/dev/tex/Props/Vase_cc_01.png",              []),
            ("/home/dev/assets/Torch_msk_preview.jpg",          []),
            ("/mnt/share/tex/Vehicle_Wheel_nml_lod1.tga",       []),
        ]
        for path, expected in cases:
            with self.subTest(path=path):   
                suffix, tokens = collect_suffixes_from_path(path, SUFFIX_ARRAY)
                self.assertEqual(suffix, expected)

    def test_three_tokens_one_not_in_array(self):
        # _区切りの3トークンのうち1つが suffix_array に無いケース
        # 位置（右端／中央／左端の不一致）をそれぞれカバー
        cases = [
            # 右端が不一致 → 何も取れない
            ("/home/dev/proj/tex/Stairs_nml_col_dummy.png",   []),

            # 中央が不一致 → 右端だけ取れる
            ("/home/dev/textures/CharacterHair_cc_BAD_msk.tga", ['msk']),

            # 左端が不一致 → 右端の2つが取れる
            ("/srv/game/tex/Tileset_lod1_mw_cc.exr",          ['mw', 'cc']),
        ]
        for path, expected in cases:
            with self.subTest(path=path):
                suffix, tokens = collect_suffixes_from_path(path, SUFFIX_ARRAY)
                self.assertEqual(suffix, expected)


if __name__ == "__main__":
    unittest.main()
