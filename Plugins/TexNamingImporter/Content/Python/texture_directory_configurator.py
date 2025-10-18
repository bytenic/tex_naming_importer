"""Utility to apply texture configuration to every texture asset under a directory.

This script enumerates all texture assets within an Unreal asset directory (e.g.
/Game/Environments) and reuses the existing ``apply_texture_property_from_config``
function so that the same validation/override flow is applied to each asset.
"""
import argparse
import sys
from pathlib import Path
from typing import Iterable, List

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from config import Config
from texture_configurator import apply_texture_property_from_config


def _require_unreal_module():
    """Return the ``unreal`` module or raise a descriptive error."""
    try:
        import unreal  # type: ignore
    except ImportError as exc:  # pragma: no cover - requires Unreal runtime
        raise RuntimeError(
            "texture_directory_configurator must be executed inside the Unreal Python runtime"
        ) from exc
    return unreal


def _normalize_dir_path(dir_path: str) -> str:
    normalized = dir_path.replace("\\", "/").strip()
    if not normalized:
        raise ValueError("dir_path must not be empty")
    if not normalized.startswith("/"):
        # Unreal asset paths always start from /Game or /Plugin, so enforce
        normalized = f"/{normalized.lstrip('/')}"
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    normalized = normalized.rstrip("/")
    if not normalized:
        raise ValueError("dir_path must point to a valid Unreal asset directory")
    return normalized


def collect_texture_asset_paths(dir_path: str, *, recursive: bool = True) -> List[str]:
    """Collect texture asset paths under ``dir_path`` using the Asset Registry."""
    unreal = _require_unreal_module()

    normalized = _normalize_dir_path(dir_path)

    registry = unreal.AssetRegistryHelpers.get_asset_registry()

    # ``ARFilter`` collects assets under the directory. ``Texture`` is the root class and
    # ``recursive_classes`` ensures that Texture2D, TextureCube, etc. are included.
    ar_filter = unreal.ARFilter(
        class_names=["Texture"],
        package_paths=[normalized],
        recursive_paths=recursive,
        recursive_classes=True,
    )

    asset_data_list = registry.get_assets(ar_filter)
    textures: List[str] = []
    for asset_data in asset_data_list:
        package_name = getattr(asset_data, "package_name", None)
        asset_name = getattr(asset_data, "asset_name", None)
        if not package_name or not asset_name:
            continue
        asset_path = f"{package_name}.{asset_name}"
        textures.append(asset_path)

    return sorted(set(textures))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="texture_directory_configurator",
        description=(
            "テクスチャ設定 CLI (ディレクトリ版)\n"
            "config_path と dir_path を指定すると、dir_path 以下のテクスチャ全てに\n"
            "apply_texture_property_from_config を実行します。"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "config_path",
        help="Config の JSON ファイルパス。例: {ProjectDir}/Config/TexNamingImporter/Config.json",
    )
    parser.add_argument(
        "dir_path",
        help="対象ディレクトリの Unreal アセットパス。例: /Game/Textures",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="サフィックスエラー時にテクスチャアセットを削除する場合は --delete を指定。",
    )
    parser.add_argument(
        "--dialog",
        action="store_true",
        help="サフィックスエラーやインポート失敗時にダイアログを表示する場合は --dialog を指定。",
    )
    parser.add_argument(
        "--non-recursive",
        action="store_true",
        help="サブディレクトリを探索せず、直下のテクスチャのみを対象にします。",
    )
    return parser


def main(argv: Iterable[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv))

    config_data = Config.load(args.config_path)
    textures = collect_texture_asset_paths(args.dir_path, recursive=not args.non_recursive)

    if not textures:
        print(f"No textures found under {args.dir_path}")
        return 0

    print(f"Found {len(textures)} textures under {args.dir_path}")
    for tex in textures:
        print(f"  - {tex}")

    return apply_texture_property_from_config(
        texture_list=textures,
        config_data=config_data,
        delete_on_suffix_error=args.delete,
        show_dialog_on_error=args.dialog,
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - minimal reporting
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
