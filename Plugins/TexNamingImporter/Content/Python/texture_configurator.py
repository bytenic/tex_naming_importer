import sys, argparse
from pathlib import Path
from typing import List, Dict

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import validator
from texture_config import overwrite_address_uv, load_params_map_json
from suffix_config import TextureSuffixConfig, load_texture_suffix_config
from type_define import AddressMode
from config import Config, TextureConfigParams
from path_utils.path_functions import *

from detail_unreal.texture_configurator_unreal import TextureConfigurator

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="texture_configurator",
        description=(
            "テクスチャ設定最小CLI\n"
            "以下の4つの位置引数を受け取り、execute_texture_config を呼び出します。\n"
            "  1) TextureSettings の JSON パス\n"
            "  2) SuffixSettings の JSON パス\n"
            "  3) DirectorySettings の JSON パス\n"
            "  4) テクスチャアセットパス（例: /Game/Textures/T_Sample.T_Sample）"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "texture_config_path",
        help="TextureSettings の JSON ファイルパス。例: {ProjectDir}/Config/TexNamingImporter/TextureSettings.json",
    )
    parser.add_argument(
        "suffix_config_path",
        help="SuffixSettings の JSON ファイルパス。例: {ProjectDir}/Config/TexNamingImporter/SuffixSettings.json",
    )
    parser.add_argument(
        "config_path",
        help="Config の JSON ファイルパス。例: {ProjectDir}/Config/TexNamingImporter/Config.json",
    )
    parser.add_argument(
        "texture_path",
        help="対象テクスチャの Unreal アセットパス。例: /Game/Textures/T_Sample.T_Sample",
    )
    return parser


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


def apply_texture_property_from_config(texture_list: List[str], texture_config_path: str, suffix_config_path: str, config_path) -> int:
    tex_settings_dict = load_params_map_json(texture_config_path)
    suffix_settings = load_texture_suffix_config(suffix_config_path)
    
    suffix_grid = validator.build_suffix_grid(suffix_settings)
    all_suffixes = [suf for row in suffix_grid for suf in row]
    config_data = Config()
    config_data = config_data.load(config_path)
    print(config_data)
    for tex_path in texture_list:
        print(f"---import begin  {tex_path} ---")
        suffixes = collect_suffixes_from_path(tex_path, all_suffixes)
        suffix_result = validator.validate_suffixes(suffixes, suffix_grid)
        print(suffix_result)  
        if suffix_result.ok:
            print("Suffix OK")
        else:
            print(f"Suffix Error: {suffix_result.error}")
            continue  # サフィックスエラーならインポートしない

        # c++側で判定するのでコメントアウト
        #is_valid_dir = validator.validate_directory(tex_path, run_directory)
        #if is_valid_dir:
        #     print("Valid Directory")
        # else:
        #     print("Invalid Directory")
        #     print(f"---import end  {tex_path} ---")
        #     continue
        texture_settings = build_texture_config_params(suffixes, tex_settings_dict, suffix_settings)
        print(f"import property: {texture_settings}")
        importer = TextureConfigurator(params=texture_settings)
        import_result_dict = importer.apply(tex_path)
        print(import_result_dict)
        if import_result_dict.get("ok"):
            print("Import Succeeded")
        else:
            print(f"Import Failed: {import_result_dict}")
        print(f"---import end  {tex_path} ---")
    return 0


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    textures = [args.texture_path]
    # execute_texture_config() 呼び出し（戻り値が int ならそれを終了コードに、そうでなければ 1）
    try:
        ret = apply_texture_property_from_config(
            texture_list=textures,
            texture_config_path=args.texture_config_path,
            suffix_config_path=args.suffix_config_path,
            config_path=args.config_path
        )
        sys.exit(int(ret) if isinstance(ret, int) else 1)
    except SystemExit:
        raise
    except Exception as e:
        # ここでは余計な処理はせず、簡単なスタックのみで終了
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
