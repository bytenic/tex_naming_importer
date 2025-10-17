import math
import sys
from pathlib import Path
from typing import Union, Dict, List, Callable, Optional
import unreal

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from config import TextureConfigParams, NumericSize
from type_define import (
    AddressMode,
    CompressionKind,
    SRGBMode,
    SizePreset,
    MipGenKind,
    TextureGroupKind, 
) 

def _get_texture_from_path(path: str) -> unreal.Texture:
    """
    /Game から始まるパスからテクスチャ(UTexture系)を取得する。
    見つからない／型が違う場合は例外を投げる。
    """
    # AssetRegistry でまず存在と型を確認
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    data = registry.get_asset_by_object_path(path)

    if not data.is_valid():
        # Registry に無い場合、EditorAssetLibrary でラストチャンス読み込み
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if asset is None:
            raise LookupError(f"Asset not found: {path!r} (normalized: {path!r})")
    else:
        asset = data.get_asset()  # ここでロード

    # 型チェック（Texture の派生だけ許可）
    # Unreal Python は isinstance も is_a も使えます。両方ケア。
    if not (isinstance(asset, unreal.Texture) or asset.is_a(unreal.Texture)):
        raise TypeError(
            f"Asset is not a Texture: {asset.get_path_name()} (class={asset.get_class().get_name()})"
        )

    # 型は Texture 基底なので、必要なら Texture2D などへキャストして使う
    return asset  # type: ignore[return-value]


def delete_texture_asset(texture_path: str) -> bool:
    """指定されたテクスチャアセットを削除する。"""
    if not texture_path:
        raise ValueError("texture_path must be non-empty")

    package_path = texture_path.split(".", 1)[0]
    editor_lib = unreal.EditorAssetLibrary

    if not editor_lib.does_asset_exist(package_path):
        unreal.log_warning(f"[TextureConfigurator] Delete skipped. Asset not found: {package_path}")
        return False

    deleted = editor_lib.delete_asset(package_path)
    if deleted:
        unreal.log(f"[TextureConfigurator] Deleted texture asset: {package_path}")
    else:
        unreal.log_error(f"[TextureConfigurator] Failed to delete texture asset: {package_path}")
    return deleted


def show_texture_configurator_dialog(
    title: str,
    message: str,
    *,
    message_type: Optional["unreal.AppMsgType"] = None,
) -> None:
    """Show a dialog in the Unreal Editor. Fallback to log if unavailable."""
    try:
        if message_type is None:
            message_type = getattr(unreal.AppMsgType, "OK", None)
        default_value = getattr(unreal.AppReturnType, "OK", None)
        if message_type is None or default_value is None:
            unreal.log_warning(
                f"[TextureConfigurator] Dialog not shown: AppMsgType/AppReturnType not available.\n{title}: {message}"
            )
            return
        unreal.EditorDialog.show_message(
            title=title,
            message=message,
            message_type=message_type,
            default_value=default_value,
        )
    except Exception as dialog_error:  # pragma: no cover - best effort logging
        unreal.log_error(
            f"[TextureConfigurator] Failed to show dialog '{title}': {dialog_error}\n{message}"
        )


class TextureConfigurator:
    """
    - __init__(*, params: TextureConfigParams) で設定値を受け取る
    - apply(texture): dataclassの内容を一括反映（Undo, post_edit_change, 保存, 共通エラハン）
    - set_address / set_max_in_game / set_compression / set_srgb: 個別反映（commit=Trueで即保存）
    """

    def __init__(self, *, params: TextureConfigParams):
        if not isinstance(params, TextureConfigParams):
            raise TypeError("params must be TextureConfigParams")
        self.params = params

    # ---------- Unreal 変換（アダプタ） ----------
    @staticmethod
    def _ua(addr: AddressMode):
        E = unreal.TextureAddress
        if addr is AddressMode.WRAP:
            for n in ("WRAP", "TA_WRAP"):
                if hasattr(E, n): return getattr(E, n)
        if addr is AddressMode.CLAMP:
            for n in ("CLAMP", "TA_CLAMP"):
                if hasattr(E, n): return getattr(E, n)
        if addr is AddressMode.MIRROR:
            for n in ("MIRROR", "TA_MIRROR"):
                if hasattr(E, n): return getattr(E, n)
        raise RuntimeError(f"Unsupported AddressMode on this engine build: {addr}")

    @staticmethod
    def _uc(kind: CompressionKind):
        E = unreal.TextureCompressionSettings
        table = {
            CompressionKind.DEFAULT:             ("DEFAULT", "TC_DEFAULT"),
            CompressionKind.NORMAL_MAP:          ("NORMALMAP", "TC_NORMALMAP"),
            CompressionKind.MASKS:               ("MASKS", "TC_MASKS"),
            CompressionKind.GRAYSCALE:           ("GRAYSCALE", "TC_GRAYSCALE"),
            CompressionKind.HDR:                 ("HDR", "TC_HDR"),
            CompressionKind.ALPHA:               ("ALPHA", "TC_ALPHA"),
            CompressionKind.EDITOR_ICON:         ("EDITORICON", "TC_EDITORICON"),
            CompressionKind.DISTANCE_FIELD_FONT: ("DISTANCE_FIELD_FONT", "TC_DISTANCE_FIELD_FONT"),
            CompressionKind.BC7:                 ("BC7", "TC_BC7"),
        }
        for name in table[kind]:
            if hasattr(E, name):
                return getattr(E, name)
        raise RuntimeError(f"Unsupported CompressionKind on this engine build: {kind}")
    
    @staticmethod
    def _um(kind: MipGenKind):
        """MipGenKind -> unreal.TextureMipGenSettings"""
        E = unreal.TextureMipGenSettings
        # 候補名（UEバージョン差吸収）
        table = {
            MipGenKind.FROM_TEXTURE_GROUP: ("FROM_TEXTURE_GROUP", "TMGS_FROM_TEXTURE_GROUP"),
            MipGenKind.NO_MIPMAPS:         ("NO_MIPMAPS", "TMGS_NO_MIPMAPS"),
            MipGenKind.SIMPLE_AVERAGE:     ("SIMPLE_AVERAGE", "TMGS_SIMPLE_AVERAGE"),
            MipGenKind.SHARPEN0:           ("SHARPEN0", "TMGS_SHARPEN0"),
            MipGenKind.SHARPEN1:           ("SHARPEN1", "TMGS_SHARPEN1"),
            MipGenKind.SHARPEN2:           ("SHARPEN2", "TMGS_SHARPEN2"),
            MipGenKind.SHARPEN3:           ("SHARPEN3", "TMGS_SHARPEN3"),
            MipGenKind.SHARPEN4:           ("SHARPEN4", "TMGS_SHARPEN4"),
            MipGenKind.SHARPEN5:           ("SHARPEN5", "TMGS_SHARPEN5"),
            MipGenKind.SHARPEN6:           ("SHARPEN6", "TMGS_SHARPEN6"),
            MipGenKind.SHARPEN7:           ("SHARPEN7", "TMGS_SHARPEN7"),
            MipGenKind.SHARPEN8:           ("SHARPEN8", "TMGS_SHARPEN8"),
        }
        names = table.get(kind, ())
        for n in names:
            if hasattr(E, n):
                return getattr(E, n)
        raise RuntimeError(f"Unsupported MipGenKind on this engine build: {kind}")

    @staticmethod
    def _utg(kind: TextureGroupKind):
        """TextureGroupKind -> unreal.TextureGroup"""
        E = unreal.TextureGroup
        table = {
            TextureGroupKind.WORLD:                 ("TEXTUREGROUP_WORLD", "WORLD"),
            TextureGroupKind.WORLD_NORMAL_MAP:      ("TEXTUREGROUP_WORLD_NORMAL_MAP", "WORLD_NORMAL_MAP"),
            TextureGroupKind.WORLD_SPECULAR:        ("TEXTUREGROUP_WORLD_SPECULAR", "WORLD_SPECULAR"),
            TextureGroupKind.CHARACTER:             ("TEXTUREGROUP_CHARACTER", "CHARACTER"),
            TextureGroupKind.CHARACTER_NORMAL_MAP:  ("TEXTUREGROUP_CHARACTER_NORMAL_MAP", "CHARACTER_NORMAL_MAP"),
            TextureGroupKind.CHARACTER_SPECULAR:    ("TEXTUREGROUP_CHARACTER_SPECULAR", "CHARACTER_SPECULAR"),
            TextureGroupKind.UI:                    ("TEXTUREGROUP_UI", "UI"),
            TextureGroupKind.LIGHTMAP:              ("TEXTUREGROUP_LIGHTMAP", "LIGHTMAP"),
            TextureGroupKind.SHADOWMAP:             ("TEXTUREGROUP_SHADOWMAP", "SHADOWMAP"),
            TextureGroupKind.SKYBOX:                ("TEXTUREGROUP_SKYBOX", "SKYBOX"),
            TextureGroupKind.VEHICLE:               ("TEXTUREGROUP_VEHICLE", "VEHICLE"),
            TextureGroupKind.CINEMATIC:             ("TEXTUREGROUP_CINEMATIC", "CINEMATIC"),
            TextureGroupKind.EFFECTS:               ("TEXTUREGROUP_EFFECTS", "EFFECTS"),
            TextureGroupKind.MEDIA:                 ("TEXTUREGROUP_MEDIA", "MEDIA"),
        }
        names = table.get(kind, ())
        for n in names:
            if hasattr(E, n):
                return getattr(E, n)
        raise RuntimeError(f"Unsupported TextureGroupKind on this engine build: {kind}")

    @staticmethod
    def _size_to_int(v: NumericSize) -> int:
        if isinstance(v, SizePreset):
            return int(v)
        if isinstance(v, int):
            return max(0, v)
        raise TypeError("max_in_game must be int or SizePreset")

    @staticmethod
    def _auto_srgb_from_compression_unreal(cs: unreal.TextureCompressionSettings) -> bool:
        E = unreal.TextureCompressionSettings
        if cs == getattr(E, "TC_NORMALMAP", object()): return False
        if cs == getattr(E, "TC_MASKS", object()): return False
        if cs == getattr(E, "TC_GRAYSCALE", object()): return False
        if cs == getattr(E, "TC_HDR", object()): return False
        if cs == getattr(E, "TC_ALPHA", object()): return False
        if cs == getattr(E, "TC_DISTANCE_FIELD_FONT", object()): return False
        if cs == getattr(E, "TC_EDITORICON", object()): return True
        if cs == getattr(E, "TC_BC7", object()): return True
        return True

    def apply(self, path_name: str) -> Dict[str, Union[bool, List[str]]]:
        """
        dataclassの内容を一括反映。
        - Undo（ScopedEditorTransaction）
        - post_edit_change / mark_package_dirty / 保存（1回）
        - 各ステップの例外を収集して返す
        """
        texture = _get_texture_from_path(path_name)
        p = self.params
        report = {"ok": True, "applied": [], "errors": []}
        revert_actions: List[Callable[[], None]] = []

        def _revert_with(setter: Callable[[], None]) -> None:
            revert_actions.append(setter)

        def _set_attr(attr: str, value) -> None:
            original = getattr(texture, attr)
            setattr(texture, attr, value)
            _revert_with(lambda texture=texture, attr=attr, original=original: setattr(texture, attr, original))

        def _set_editor_property(name: str, value) -> None:
            original = texture.get_editor_property(name)
            texture.set_editor_property(name, value)
            _revert_with(
                lambda texture=texture, name=name, original=original: texture.set_editor_property(name, original)
            )

        if not isinstance(texture, unreal.Texture):
            msg = "apply(): first argument must be unreal.Texture"
            unreal.log_error(msg)
            report.update(ok=False, errors=[msg])
            return report

        trans = unreal.ScopedEditorTransaction("Configure Texture (Batch Apply)")
        try:
            texture.modify()

            # 1) Address
            if p.address_u is not None and p.address_v is not None:
                try:
                    _set_attr("address_x", self._ua(p.address_u))
                    _set_attr("address_y", self._ua(p.address_v))
                    if p.address_z is not None and hasattr(texture, "address_z"):
                        _set_attr("address_z", self._ua(p.address_z))
                    report["applied"].append("address")
                except Exception as e:
                    report["ok"] = False
                    report["errors"].append(f"address: {e}")

            # 2) Max In-Game
            if p.max_in_game is not None:
                try:
                    size = self._size_to_int(p.max_in_game)
                    if p.enforce_pow2 and size > 0:
                        size = 1 << int(math.log2(size))
                    if size > 0:
                        size = max(16, min(size, 16384))
                    if hasattr(texture, "max_texture_size"):
                        _set_attr("max_texture_size", size)
                    else:
                        _set_editor_property("MaxTextureSize", size)
                    report["applied"].append("max_in_game")
                except Exception as e:
                    report["ok"] = False
                    report["errors"].append(f"max_in_game: {e}")

            # 3) Compression（sRGB AUTO 参照元）
            if p.compression is not None:
                try:
                    _set_attr("compression_settings", self._uc(p.compression))
                    report["applied"].append("compression")
                except Exception as e:
                    report["ok"] = False
                    report["errors"].append(f"compression: {e}")

            # 4) sRGB
            if p.srgb is not None:
                try:
                    if p.srgb is SRGBMode.AUTO:
                        cs = getattr(texture, "compression_settings", None)
                        if not isinstance(cs, unreal.TextureCompressionSettings):
                            raise RuntimeError("failed to read compression_settings for AUTO sRGB")
                        desired = self._auto_srgb_from_compression_unreal(cs)
                    else:
                        desired = (p.srgb is SRGBMode.ON)

                    if hasattr(texture, "srgb"):
                        _set_attr("srgb", bool(desired))
                    else:
                        _set_editor_property("SRGB", bool(desired))
                    report["applied"].append("srgb")
                except Exception as e:
                    report["ok"] = False
                    report["errors"].append(f"srgb: {e}")

            # 5) TextureGroup（LODGroup
            try:
                tg = self._utg(p.texture_group)
                # C++プロパティ名は LODGroup。Python では set_editor_property が確実。
                _set_editor_property("LODGroup", tg)
                report["applied"].append("texture_group")
            except Exception as e:
                report["ok"] = False
                report["errors"].append(f"texture_group: {e}")

            # === 6) MipGenSettings ===
            try:
                mg = self._um(p.mip_gen)
                _set_editor_property("MipGenSettings", mg)
                report["applied"].append("mip_gen")
            except Exception as e:
                report["ok"] = False
                report["errors"].append(f"mip_gen: {e}")

            # 一括反映
            path = texture.get_path_name()
            if report["ok"]:
                unreal.EditorAssetLibrary.save_loaded_asset(texture)
                unreal.log(f"[TextureConfigurator] Applied to {path} ({', '.join(report['applied']) or 'no-op'})")
            else:
                # Rollback all modifications done so far
                for revert in reversed(revert_actions):
                    try:
                        revert()
                    except Exception as revert_error:
                        report["errors"].append(f"rollback: {revert_error}")
                report["applied"] = []
                cancel = getattr(trans, "cancel", None)
                if callable(cancel):
                    try:
                        cancel()
                    except Exception as cancel_error:
                        report["errors"].append(f"transaction_cancel: {cancel_error}")
                unreal.log_warning(f"[TextureConfigurator] Applied with errors on {path}: {report['errors']}")

            return report
        finally:
            del trans
