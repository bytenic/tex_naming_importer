import sys
from pathlib import Path
from typing import List, Dict

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import settings_importer
import validator
from texture_config import TextureConfigParams, overwrite_address_uv
from suffix_config import TextureSuffixConfig
from type_define import AddressMode
from path_utils.path_functions import *
from import_unreal.texture_importer_unreal import TextureConfigurator

def get_address_settings_from_suffix(suffixes: List[str], suffix_settings: TextureSuffixConfig):
    for suf in suffixes:
        if suffix_settings.has_2d(suf):
            return suffix_settings.get_uv(suf)
        if suffix_settings.has_3d(suf):
            return suffix_settings.get_uvw(suf)
    return (AddressMode.WRAP, AddressMode.WRAP)

def get_texture_settings_from_suffixes(suffixes: List[str],
                                        texture_settings: Dict[str, TextureConfigParams],
                                        suffix_settings: TextureSuffixConfig):
    for suf in suffixes:
        if suf in texture_settings:
            return texture_settings[suf]
    return TextureConfigParams()


def build_texture_config_params(suffixes: List[str],
                                tex_settings_dict: Dict[str, TextureConfigParams],
                                suffix_settings: TextureSuffixConfig)-> TextureConfigParams:
    base_settings = get_texture_settings_from_suffixes(suffixes, tex_settings_dict, suffix_settings)
    # 現状はTex2Dのみ対応
    address_u, address_v = get_address_settings_from_suffix(suffixes, suffix_settings)
    return overwrite_address_uv(base_settings, address_u, address_v)


def main(texture_list: List[str], texture_config_path: str, suffix_config_path: str) -> int:
    tex_settings_dict, suffix_settings = settings_importer.load_settings(
        texture_config_path,
        suffix_config_path
    )
    valid_directory = ["/Game/VFX/", "/Game/Debug"]
    suffix_grid = validator.build_suffix_grid(suffix_settings)
    all_suffixes = [suf for row in suffix_grid for suf in row]
    for tex_path in texture_list:
        print(f"---import start  {tex_path} ---")
        suffixes = collect_suffixes_from_path(tex_path, all_suffixes)
        suffix_result = validator.validate_suffixes(suffixes, suffix_grid)
        print(suffix_result)  
        if suffix_result.ok:
            print("Suffix OK")
        else:
            print(f"Suffix Error: {suffix_result.error}")
            continue  # サフィックスエラーならインポートしない

        is_valid_dir = validator.validate_directory(tex_path, valid_directory)
        if is_valid_dir:
            print("Valid Directory")
        else:
            print("Invalid Directory")
            print(f"---import end  {tex_path} ---")
            continue
        address_mode = get_address_settings_from_suffix(suffixes, suffix_settings)
        print(address_mode)
        texture_settings = build_texture_config_params(suffixes, tex_settings_dict, suffix_settings)
        print(texture_settings)
        importer = TextureConfigurator(params=texture_settings)
        importer.apply(tex_path)
        print(f"---import end  {tex_path} ---")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: <script> <texture_config_path> <suffix_config_path> <texture_path>")
        sys.exit(1)
    texture_config = sys.argv[1]
    suffix_config = sys.argv[2]
    texture_path = sys.argv[3]
    sys.exit(main([texture_path], texture_config, suffix_config))
