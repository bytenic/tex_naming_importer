"""
サフィックスと Config からテクスチャ設定を適用する CLI モジュール。
"""

import sys, argparse
import traceback
from pathlib import Path
from typing import List, Dict

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import validator
from type_define import AddressMode
from config import Config, TextureConfigParams, override_address_uv, override_subuv_max_in_game
from path_utils.path_functions import *

from detail_unreal.texture_configurator_unreal import (
    TextureConfigurator,
    delete_texture_asset,
    show_texture_configurator_dialog,
)

SUBUV_PATTERN = r'^[1-9]\d*[xX][1-9]\d*$'  # 例: 8x8, 4x4, 1x8

def build_parser() -> argparse.ArgumentParser:
    """
    コマンドライン引数のパーサを作成して返す。

    Returns:
        argparse.ArgumentParser: 設定済みの引数パーサ。
    """
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
    parser.add_argument(
        "--delete",
        help="サフィックスエラー時にテクスチャアセットを削除する場合は --delete を指定。",
        action="store_true"
    )
    parser.add_argument(
        "--dialog",
        help="サフィックスエラーやインポート失敗時にダイアログを表示する場合は --dialog を指定。",
        action="store_true"
    )
    return parser


def get_address_settings_from_suffix(suffixes: List[str], config_data: Config):
    """
    サフィックスからアドレスモード（UV/UVW）の設定を決定する。

    Args:
        suffixes (List[str]): 対象テクスチャから抽出したサフィックス一覧。
        config_data (Config): サフィックス設定を持つ Config。

    Returns:
        tuple: (AddressMode, AddressMode) の組。
    """
    for suf in suffixes:
        if config_data.has_suffix_2d(suf):
            return config_data.get_uv(suf)
        if config_data.has_suffix_3d(suf):
            return config_data.get_uvw(suf)
    return (AddressMode.WRAP, AddressMode.WRAP)


def get_texture_settings_from_suffixes(suffixes: List[str],
                                        texture_settings: Dict[str, TextureConfigParams]):
    """
    サフィックスに一致するテクスチャ設定を取得する。

    Args:
        suffixes (List[str]): 対象テクスチャから抽出したサフィックス一覧。
        texture_settings (Dict[str, TextureConfigParams]): サフィックス別設定の辞書。

    Returns:
        TextureConfigParams: 一致した設定。該当がなければデフォルト値。
    """
    for suf in suffixes:
        if suf in texture_settings:
            return texture_settings[suf]
    return TextureConfigParams()


def build_texture_config_params(suffixes: List[str],
                                tex_settings_dict: Dict[str, TextureConfigParams],
                                config_data: Config)-> TextureConfigParams:
    """
    サフィックスと Config を元に最終的な設定値を生成する。

    Args:
        suffixes (List[str]): 対象テクスチャから抽出したサフィックス一覧。
        tex_settings_dict (Dict[str, TextureConfigParams]): サフィックス別設定の辞書。
        config_data (Config): UV/UVW などのアドレス設定を含む Config。

    Returns:
        TextureConfigParams: アドレス設定を反映した最終設定。
    """
    base_settings = get_texture_settings_from_suffixes(suffixes, tex_settings_dict)
    # 現状はTex2Dのみ対応
    print(f"Base settings from suffixes: {base_settings}")
    address_u, address_v = get_address_settings_from_suffix(suffixes, config_data)
    return override_address_uv(base_settings, address_u, address_v)


def apply_texture_property_from_config(
    texture_list: List[str],
    config_data: Config,
    delete_on_suffix_error: bool = False,
    show_dialog_on_error: bool = False,
) -> int:
    """
    設定を適用し、エラー時は削除やダイアログ表示を行う。

    Args:
        texture_list (List[str]): Unreal のテクスチャパス一覧。
        config_data (Config): サフィックス規則と設定を含む Config。
        delete_on_suffix_error (bool): サフィックス不正時に削除を試みるか。
        show_dialog_on_error (bool): エラー時にダイアログを表示するか。

    Returns:
        int: 終了コード。通常は 0。
    """
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
            if show_dialog_on_error:
                show_texture_configurator_dialog(
                    title="Texture Configurator - Suffix Error",
                    message=(
                        f"テクスチャ {tex_path} のサフィックスが不正です。\n"
                        f"詳細: {suffix_result.error}"
                    ),
                )
            if delete_on_suffix_error:
                try:
                    deleted = delete_texture_asset(tex_path)
                    print(f"Delete Texture ({'Succeeded' if deleted else 'Failed'}): {tex_path}")
                except Exception as delete_error:
                    print(f"Delete Texture Error: {delete_error}")
            continue  # サフィックスエラーならインポートしない

        texture_settings = build_texture_config_params(suffixes, config_data.texture_config, config_data)
        if config_data.enable_subuv_texture_override: 
            if validator.regex_any_match(SUBUV_PATTERN, tokens):
                texture_settings = override_subuv_max_in_game(texture_settings, config_data.subuv_max_in_game)
                print("suffix override")
        
        print(f"import property: {texture_settings}")
        importer = TextureConfigurator(params=texture_settings)
        try:
            import_result_dict = importer.apply(tex_path)
        except Exception as import_error:
            tb = traceback.format_exc()
            print(f"Import Exception: {import_error}\n{tb}")
            if show_dialog_on_error:
                show_texture_configurator_dialog(
                    title="Texture Configurator - Import Exception",
                    message=(
                        f"テクスチャ {tex_path} の設定適用中に例外が発生しました。\n"
                        f"Exception: {import_error}\n"
                        f"Traceback:\n{tb}"
                    ),
                )
            continue
        print(import_result_dict)
        if import_result_dict.get("ok"):
            print("Import Succeeded")
        else:
            print(f"Import Failed: {import_result_dict}")
            if show_dialog_on_error:
                show_texture_configurator_dialog(
                    title="Texture Configurator - Import Failed",
                    message=(
                        f"テクスチャ {tex_path} の設定適用に失敗しました。\n"
                        f"結果: {import_result_dict}"
                    ),
                )
        print(f"---import end  {tex_path} ---")
    return 0


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    textures = [args.texture_path]
    # execute_texture_config() 呼び出し（戻り値が int ならそれを終了コードに、そうでなければ 1）
    try:
        config_data = Config.load(args.config_path)
        ret = apply_texture_property_from_config(
            texture_list=textures,
            config_data=config_data,
            delete_on_suffix_error=args.delete,
            show_dialog_on_error=args.dialog
        )
        sys.exit(int(ret) if isinstance(ret, int) else 1)
    except SystemExit:
        raise
    except Exception as e:
        # ここでは余計な処理はせず、簡単なスタックのみで終了
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
