import sys, argparse
from pathlib import Path
from typing import List, Dict

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import validator
from type_define import AddressMode
from config import Config, TextureConfigParams, override_address_uv, override_subuv_max_in_game
from path_utils.path_functions import *

from detail_unreal.texture_configurator_unreal import TextureConfigurator

SUBUV_PATTERN = r'^[1-9]\d*[xX][1-9]\d*$'  # 例: 8x8, 4x4, 1x8

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="texture_configurator",
        description=(
            "テクスチャ設定最小CLI\n"
            "以下の4つの位置引数を受け取り、execute_texture_config を呼び出します。\n"
            "  1) Configファイル の JSON パス\n"
            "  2) テクスチャアセットパス（例: /Game/Textures/T_Sample.T_Sample）"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
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


def get_address_settings_from_suffix(suffixes: List[str], config_data: Config):
    for suf in suffixes:
        if config_data.has_suffix_2d(suf):
            return config_data.get_uv(suf)
        if config_data.has_suffix_3d(suf):
            return config_data.get_uvw(suf)
    return (AddressMode.WRAP, AddressMode.WRAP)


def get_texture_settings_from_suffixes(suffixes: List[str],
                                        texture_settings: Dict[str, TextureConfigParams]):
    for suf in suffixes:
        if suf in texture_settings:
            return texture_settings[suf]
    return TextureConfigParams()


def build_texture_config_params(suffixes: List[str],
                                tex_settings_dict: Dict[str, TextureConfigParams],
                                config_data: Config)-> TextureConfigParams:
    base_settings = get_texture_settings_from_suffixes(suffixes, tex_settings_dict)
    # 現状はTex2Dのみ対応
    print(f"Base settings from suffixes: {base_settings}")
    address_u, address_v = get_address_settings_from_suffix(suffixes, config_data)
    return override_address_uv(base_settings, address_u, address_v)


def apply_texture_property_from_config(texture_list: List[str], config_path: str) -> int:
    config_data = Config.load(config_path)
    suffix_grid = config_data.build_suffix_grid()
    #print(f'suffix:{suffix_grid}')
    all_suffixes = [suf for row in suffix_grid for suf in row]
    #print(config_data)
    for tex_path in texture_list:
        print(f"---import begin  {tex_path} ---")
        suffixes,tokens = collect_suffixes_from_path(tex_path, all_suffixes)
        #print(f"collected suffixes: {suffixes}")
        print(tokens)
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
        texture_settings = build_texture_config_params(suffixes, config_data.texture_config, config_data)
        if config_data.enable_subuv_texture_override: 
            if validator.regex_any_match(SUBUV_PATTERN, tokens):
                texture_settings = override_subuv_max_in_game(texture_settings, config_data.subuv_max_in_game)
                print("suffix override")
        
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
            config_path=args.config_path
        )
        sys.exit(int(ret) if isinstance(ret, int) else 1)
    except SystemExit:
        raise
    except Exception as e:
        # ここでは余計な処理はせず、簡単なスタックのみで終了
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
