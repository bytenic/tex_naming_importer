import math
import unreal
from enum import Enum, IntEnum
from typing import Optional, Union, Dict, List
from type_define import (
    TextureConfigParams,
    AddressMode,
    CompressionKind,
    SRGBMode,
    SizePreset,
    NumericSize
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

    # ---------- 個別適用（細粒度） ----------
    def set_address(self, texture: unreal.Texture, u: AddressMode, v: AddressMode, *, z: Optional[AddressMode] = None, commit: bool = True):
        if not isinstance(texture, unreal.Texture):
            raise TypeError("texture must be unreal.Texture")
        ux = self._ua(u)
        vy = self._ua(v)
        zz = self._ua(z) if z is not None else None

        trans = unreal.ScopedEditorTransaction("Set Texture Address (U/V[/Z])") if commit else None
        try:
            texture.modify()
            texture.address_x = ux
            texture.address_y = vy
            if zz is not None and hasattr(texture, "address_z"):
                texture.address_z = zz

            if commit:
                texture.post_edit_change()
                texture.mark_package_dirty()
                if self.params.save:
                    unreal.EditorAssetLibrary.save_loaded_asset(texture)
                if not self.params.silent:
                    msg = f"[SetTextureAddress] {texture.get_path_name()} X={ux} Y={vy}" + (f" Z={zz}" if zz else "")
                    unreal.log(msg)
        finally:
            if trans is not None:
                del trans

    def set_max_in_game(self, texture: unreal.Texture, max_size: NumericSize, *, enforce_pow2: bool = False, commit: bool = True):
        if not isinstance(texture, unreal.Texture):
            raise TypeError("texture must be unreal.Texture")
        size = self._size_to_int(max_size)
        if enforce_pow2 and size > 0:
            size = 1 << int(math.log2(size))  # 下方丸め
        if size > 0:
            size = max(16, min(size, 16384))

        trans = unreal.ScopedEditorTransaction("Set Texture Max In-Game Size") if commit else None
        try:
            texture.modify()
            if hasattr(texture, "max_texture_size"):
                texture.max_texture_size = size
            else:
                texture.set_editor_property("MaxTextureSize", size)

            if commit:
                texture.post_edit_change()
                texture.mark_package_dirty()
                if self.params.save:
                    unreal.EditorAssetLibrary.save_loaded_asset(texture)
                if not self.params.silent:
                    human = "Auto (no cap)" if size == 0 else f"{size}px"
                    unreal.log(f"[SetTextureMaxInGame] {texture.get_path_name()} MaxTextureSize={human}")
        finally:
            if trans is not None:
                del trans

    def set_compression(self, texture: unreal.Texture, compression: CompressionKind, *, commit: bool = True):
        if not isinstance(texture, unreal.Texture):
            raise TypeError("texture must be unreal.Texture")
        cs = self._uc(compression)

        trans = unreal.ScopedEditorTransaction("Set Texture Compression") if commit else None
        try:
            texture.modify()
            texture.compression_settings = cs

            if commit:
                texture.post_edit_change()
                texture.mark_package_dirty()
                if self.params.save:
                    unreal.EditorAssetLibrary.save_loaded_asset(texture)
                if not self.params.silent:
                    unreal.log(f"[SetTextureCompression] {texture.get_path_name()} Compression={cs}")
        finally:
            if trans is not None:
                del trans

    def set_srgb(self, texture: unreal.Texture, mode: SRGBMode, *, commit: bool = True):
        if not isinstance(texture, unreal.Texture):
            raise TypeError("texture must be unreal.Texture")

        if mode is SRGBMode.AUTO:
            cs = getattr(texture, "compression_settings", None)
            if not isinstance(cs, unreal.TextureCompressionSettings):
                raise RuntimeError("failed to read texture.compression_settings for AUTO sRGB")
            desired = self._auto_srgb_from_compression_unreal(cs)
        else:
            desired = (mode is SRGBMode.ON)

        trans = unreal.ScopedEditorTransaction("Set Texture sRGB") if commit else None
        try:
            texture.modify()
            if hasattr(texture, "srgb"):
                texture.srgb = bool(desired)
            else:
                texture.set_editor_property("SRGB", bool(desired))

            if commit:
                texture.post_edit_change()
                texture.mark_package_dirty()
                if self.params.save:
                    unreal.EditorAssetLibrary.save_loaded_asset(texture)
                if not self.params.silent:
                    unreal.log(f"[SetTextureSRGB] {texture.get_path_name()} sRGB={'ON' if desired else 'OFF'}")
        finally:
            if trans is not None:
                del trans

    # ---------- 一括適用（共通エラハン） ----------
    def apply(self, texture: unreal.Texture) -> Dict[str, Union[bool, List[str]]]:
        """
        dataclassの内容を一括反映。
        - Undo（ScopedEditorTransaction）
        - post_edit_change / mark_package_dirty / 保存（1回）
        - 各ステップの例外を収集して返す
        """
        p = self.params
        report = {"ok": True, "applied": [], "errors": []}

        if not isinstance(texture, unreal.Texture):
            msg = "apply(): first argument must be unreal.Texture"
            if not p.silent:
                unreal.log_error(msg)
            report.update(ok=False, errors=[msg])
            return report

        trans = unreal.ScopedEditorTransaction("Configure Texture (Batch Apply)")
        try:
            texture.modify()

            # 1) Address
            if p.address_u is not None and p.address_v is not None:
                try:
                    texture.address_x = self._ua(p.address_u)
                    texture.address_y = self._ua(p.address_v)
                    if p.address_z is not None and hasattr(texture, "address_z"):
                        texture.address_z = self._ua(p.address_z)
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
                        texture.max_texture_size = size
                    else:
                        texture.set_editor_property("MaxTextureSize", size)
                    report["applied"].append("max_in_game")
                except Exception as e:
                    report["ok"] = False
                    report["errors"].append(f"max_in_game: {e}")

            # 3) Compression（sRGB AUTO 参照元）
            if p.compression is not None:
                try:
                    texture.compression_settings = self._uc(p.compression)
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
                        texture.srgb = bool(desired)
                    else:
                        texture.set_editor_property("SRGB", bool(desired))
                    report["applied"].append("srgb")
                except Exception as e:
                    report["ok"] = False
                    report["errors"].append(f"srgb: {e}")

            # 一括反映
            texture.post_edit_change()
            texture.mark_package_dirty()
            if p.save:
                unreal.EditorAssetLibrary.save_loaded_asset(texture)

            if not p.silent:
                path = texture.get_path_name()
                if report["ok"]:
                    unreal.log(f"[TextureConfigurator] Applied to {path} ({', '.join(report['applied']) or 'no-op'})")
                else:
                    unreal.log_warning(f"[TextureConfigurator] Applied with errors on {path}: {report['errors']}")

            return report
        finally:
            del trans
