from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import json

from type_define import (
    AddressMode,        # テクスチャのアドレスモード（CLAMP/WRAP/MIRROR 等）
    CompressionKind,    # 圧縮種別（BC7 等）
    SRGBMode,           # sRGB の扱い（ON/OFF/FromSource 等）
    SizePreset,         # サイズ指定のプリセット（数値化可能）
    MipGenKind,         # MipMap 生成モード（FromTextureGroup 等）
    TextureGroupKind,   # Texture Group 指定（World 等）
)

# ---------- 型エイリアス ----------
AddressPair   = Tuple[AddressMode, AddressMode]                 # 2D（U, V）
AddressTriple = Tuple[AddressMode, AddressMode, AddressMode]    # 3D（U, V, W）
NumericSize   = Union[int, SizePreset]

# =========================
# 個別タイプ設定: TextureConfigParams
# =========================
@dataclass
class TextureConfigParams:
    """各テクスチャタイプごとの設定パラメータ。

    - address_u/v/z: アドレスモード（2D は U/V、3D は U/V/W）
    - max_in_game  : ゲーム内の最大サイズ（0 または None で未指定/自動）
    - enforce_pow2 : 2 の冪サイズを強制するか
    - compression  : 圧縮形式
    - srgb         : sRGB 設定
    - mip_gen      : MipMap 生成モード（無効な値は読み込み時に例外）
    - texture_group: Texture Group（無効な値は読み込み時に例外）
    """
    address_u: Optional[AddressMode] = None
    address_v: Optional[AddressMode] = None
    address_z: Optional[AddressMode] = None

    max_in_game: Optional[int] = None  # 0（または None）は未指定/自動を示す
    enforce_pow2: bool = False

    compression: Optional[CompressionKind] = None
    srgb: Optional[SRGBMode] = None

    mip_gen: MipGenKind = MipGenKind.FROM_TEXTURE_GROUP
    texture_group: TextureGroupKind = TextureGroupKind.WORLD

    # ---- 内部: 列挙体・値変換ヘルパ ----
    @staticmethod
    def _enum(enum_cls, name: Optional[Union[str, int]]):
        """JSON 文字列/整数 → 列挙体 への変換（無効値は ValueError）。"""
        if name is None:
            return None
        if isinstance(name, int):
            # 整数での指定も許容（値に一致するメンバを探索）
            for m in enum_cls:
                if getattr(m, "value", None) == name:
                    return m
            raise ValueError(f"未知の {enum_cls.__name__} 整数値: {name}")
        if isinstance(name, str):
            s = name.strip()
            try:
                return enum_cls[s]
            except KeyError as e:
                raise ValueError(f"未知の {enum_cls.__name__} 名称: {s}") from e
        raise TypeError(f"{enum_cls.__name__} は文字列または整数で指定してください")

    @staticmethod
    def _size_to_int(v: Optional[Union[int, str, SizePreset]]) -> Optional[int]:
        """サイズ指定を int に正規化する。0 は自動扱い。"""
        if v is None:
            return None
        if isinstance(v, SizePreset):
            return int(v)
        if isinstance(v, int):
            return max(0, v)
        if isinstance(v, str):
            s = v.strip().upper()
            if s == "AUTO":
                return 0
            # "P1024" などの表記を許容
            if s.startswith("P") and s[1:].isdigit():
                return max(0, int(s[1:]))
            if s.isdigit():
                return max(0, int(s))
        raise ValueError("max_in_game は 0 以上の整数 または 'AUTO'/'P####' を指定してください")

    @classmethod
    def from_dict(cls, d: dict) -> "TextureConfigParams":
        """辞書から TextureConfigParams を生成（検証込み）。"""
        max_px = cls._size_to_int(d.get("max_in_game"))
        return cls(
            address_u=cls._enum(AddressMode, d.get("address_u")),
            address_v=cls._enum(AddressMode, d.get("address_v")),
            address_z=cls._enum(AddressMode, d.get("address_z")),
            max_in_game=max_px,
            enforce_pow2=bool(d.get("enforce_pow2", False)),
            compression=cls._enum(CompressionKind, d.get("compression")),
            srgb=cls._enum(SRGBMode, d.get("srgb")),
            mip_gen=cls._enum(MipGenKind, d.get("mip_gen")) or MipGenKind.FROM_TEXTURE_GROUP,
            texture_group=cls._enum(TextureGroupKind, d.get("texture_group")) or TextureGroupKind.WORLD
        )

    def to_dict(self, *, minimal: bool = True) -> dict:
        """辞書に変換。minimal=True の場合は None を出力しない。"""
        def _enum_name(e: Optional[object]) -> Optional[str]:
            return None if e is None else e.name

        out = {
            "address_u": _enum_name(self.address_u),
            "address_v": _enum_name(self.address_v),
            "address_z": _enum_name(self.address_z),
            "max_in_game": None if self.max_in_game is None else max(0, int(self.max_in_game)),
            "enforce_pow2": bool(self.enforce_pow2) if self.max_in_game is not None else None,
            "compression": _enum_name(self.compression),
            "srgb": _enum_name(self.srgb),
            "mip_gen": _enum_name(self.mip_gen),
            "texture_group": _enum_name(self.texture_group)
        }
        return {k: v for k, v in out.items() if not minimal or v is not None}


# =========================
# サフィックス（2D/3D）用ユーティリティ
# =========================
def _to_addr(x: Union[str, AddressMode]) -> AddressMode:
    """文字列（列挙名）または列挙体を AddressMode に正規化。"""
    if isinstance(x, AddressMode):
        return x
    if isinstance(x, str):
        return AddressMode[x.strip().upper()]
    raise TypeError(f"アドレス要素は str または AddressMode を指定してください: {type(x).__name__}")


def _parse_2d(val) -> AddressPair:
    """[U, V] 形式のリスト/タプルを AddressPair に変換。"""
    if not isinstance(val, (list, tuple)) or len(val) != 2:
        raise ValueError(f"2D アドレスは長さ 2 のリスト/タプルで指定してください: {val!r}")
    return (_to_addr(val[0]), _to_addr(val[1]))


def _parse_3d(val) -> AddressTriple:
    """[U, V, W] 形式のリスト/タプルを AddressTriple に変換。"""
    if not isinstance(val, (list, tuple)) or len(val) != 3:
        raise ValueError(f"3D アドレスは長さ 3 のリスト/タプルで指定してください: {val!r}")
    return (_to_addr(val[0]), _to_addr(val[1]), _to_addr(val[2]))


# =========================
# ルート統合設定: Config
# =========================
@dataclass
class Config:
    """ツール全体の統合設定。

    JSON 構造（例、ルート直下のキー）:
      - run_dir            : List[str]        … 実行対象のルートディレクトリ群（新規追加）
      - texture_type       : List[str]        … 対象のテクスチャ種別（例: col/msk/nml 等）
      - address_suffix_2d  : Dict[str, [U,V]] … 2D 用のサフィックス→(U,V) 対応表
      - address_suffix_3d  : Dict[str, [U,V,W]]（任意）… 3D 用のサフィックス→(U,V,W) 対応表
      - suffix_index       : List[str]        … サフィックス検索順や優先度の定義
      - texture_config     : Dict[str, TextureConfigParams 相当の dict]
    """
    run_dir: List[str] = field(default_factory=list)

    # サフィックス関連（2D/3D を統合）
    texture_type: List[str] = field(default_factory=list)
    address_suffix_2d: Dict[str, AddressPair] = field(default_factory=dict)
    address_suffix_3d: Dict[str, AddressTriple] = field(default_factory=dict)
    suffix_index: List[str] = field(default_factory=list)

    # テクスチャタイプごとの詳細設定
    texture_config: Dict[str, TextureConfigParams] = field(default_factory=dict)

    enable_subuv_texture_override: bool = False
    subuv_max_in_game: NumericSize = 2048

    # ---------- 読み書き ----------
    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """辞書（JSON読込結果）から Config を生成（検証込み）。"""
        if not isinstance(data, dict):
            raise TypeError("ルートは dict である必要があります")

        # run_dir の検証
        run_dir = data.get("run_dir", [])
        if not (isinstance(run_dir, list) and all(isinstance(x, str) for x in run_dir)):
            raise ValueError("'run_dir' は List[str] で指定してください")

        # texture_type の検証
        tt = data.get("texture_type")
        if not isinstance(tt, list) or not all(isinstance(x, str) for x in tt or []):
            raise ValueError("'texture_type' は List[str] で指定してください")

        # サフィックスマップ（2D/3D）
        map2d: Dict[str, AddressPair] = {}
        map3d: Dict[str, AddressTriple] = {}

        # 後方互換: 2/3 要素混在の "address_suffix" を受理
        raw_mixed = data.get("address_suffix")
        if isinstance(raw_mixed, dict):
            for k, v in raw_mixed.items():
                if isinstance(v, (list, tuple)):
                    if len(v) == 2:
                        map2d[k] = _parse_2d(v)
                    elif len(v) == 3:
                        map3d[k] = _parse_3d(v)
                    else:
                        raise ValueError(f"address_suffix[{k}] の長さは 2 または 3 にしてください")
                else:
                    raise ValueError(f"address_suffix[{k}] は list/tuple で指定してください")

        # 明示的な 2D/3D キーがある場合はそれを優先
        raw_2d = data.get("address_suffix_2d")
        if isinstance(raw_2d, dict):
            for k, v in raw_2d.items():
                map2d[k] = _parse_2d(v)

        raw_3d = data.get("address_suffix_3d")
        if isinstance(raw_3d, dict):
            for k, v in raw_3d.items():
                map3d[k] = _parse_3d(v)

        if not map2d and not map3d:
            # 完全に空は原則エラー（必要ならここを緩めても良い）
            raise ValueError("2D/3D いずれのサフィックス対応表も見つかりません")

        # suffix_index の検証
        suf_index = data.get("suffix_index")
        if not isinstance(suf_index, list) or not all(isinstance(x, str) for x in suf_index or []):
            raise ValueError("'suffix_index' は List[str] で指定してください")

        # texture_config ブロックの検証と構築
        raw_cfg = data.get("texture_config")
        if not isinstance(raw_cfg, dict):
            raise ValueError("'texture_config' はオブジェクトで指定してください")

        params_map: Dict[str, TextureConfigParams] = {}
        for key, val in raw_cfg.items():
            if not isinstance(val, dict):
                raise ValueError(f"texture_config['{key}'] はオブジェクトで指定してください")
            params_map[key] = TextureConfigParams.from_dict(val)

        enable_subuv_texture_override = bool(data.get("enable_subuv_texture_override", False))
        subuv_max_in_game = int(data.get("subuv_max_in_game", 2048))

        return cls(
            run_dir=list(run_dir),
            texture_type=list(tt),
            address_suffix_2d=map2d,
            address_suffix_3d=map3d,
            suffix_index=list(suf_index),
            texture_config=params_map,
            enable_subuv_texture_override=enable_subuv_texture_override,
            subuv_max_in_game=subuv_max_in_game
        )

    def to_dict(self) -> dict:
        """辞書（JSON化）に変換。列挙体は name（文字列）で書き出し。"""
        out = {
            "run_dir": list(self.run_dir),
            "texture_type": list(self.texture_type),
            "suffix_index": list(self.suffix_index),
            "texture_config": {k: v.to_dict(minimal=True) for k, v in self.texture_config.items()},
        }
        if self.address_suffix_2d:
            out["address_suffix_2d"] = {k: [u.name, v.name] for k, (u, v) in self.address_suffix_2d.items()}
        if self.address_suffix_3d:
            out["address_suffix_3d"] = {k: [u.name, v.name, w.name] for k, (u, v, w) in self.address_suffix_3d.items()}
        
        if self.enable_subuv_texture_override:
            out["enable_subuv_texture_override"] = self.enable_subuv_texture_override
        if self.subuv_max_in_game is not None:
            out["subuv_max_in_game"] = self.subuv_max_in_game
            
        return out
    
    def build_suffix_grid(self)->List[List[str]]:
        """
        suffix_index の順で各カテゴリの許容キー一覧を収集し、二次元配列として返す。
        行 = suffix_index の順
        列 = その行（カテゴリ）の候補キー
        """
        grid: List[List[str]] = []
        for cat in self.suffix_index:
            if(hasattr(self, cat)):
                attr = getattr(self, cat)
                keys = []
                if isinstance(attr, dict):
                    keys = list(attr.keys())
                elif isinstance(attr, list):
                    keys = list(attr)
                grid.append(keys)
        return grid

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> "Config":
        """JSON ファイルから Config を読み込む。"""
        p = Path(file_path)
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save(self, file_path: Union[str, Path], *, indent: int = 2, ensure_ascii: bool = False) -> None:
        """Config を JSON として保存する。"""
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=indent, ensure_ascii=ensure_ascii)

    def has_suffix_2d(self, key: str) -> bool:
        """与えられたキーが 2D サフィックス表に存在するか。"""
        return key in self.address_suffix_2d

    def has_suffix_3d(self, key: str) -> bool:
        """与えられたキーが 3D サフィックス表に存在するか。"""
        return key in self.address_suffix_3d

    def get_uv(self, key: str) -> AddressPair:
        """キーに対する (U, V) を取得。3D の場合は W を捨てて返す。"""
        if key in self.address_suffix_2d:
            return self.address_suffix_2d[key]
        if key in self.address_suffix_3d:
            u, v, _ = self.address_suffix_3d[key]
            return (u, v)
        raise KeyError(key)

    def get_uvw(self, key: str) -> AddressTriple:
        """キーに対する (U, V, W) を取得。2D の場合は (U, V, V) として拡張。"""
        if key in self.address_suffix_3d:
            return self.address_suffix_3d[key]
        if key in self.address_suffix_2d:
            u, v = self.address_suffix_2d[key]
            return (u, v, v)  # 2D → 3D は V を W に流用（ポリシーに応じて変更可）
        raise KeyError(key)


def override_address_uv(params: TextureConfigParams, u: AddressMode, v: AddressMode) -> TextureConfigParams:
    """
    TextureConfigParams の address_u / address_v を“破壊的（in-place）”に上書きします。
    clear_z=True の場合、address_z を None にクリアします（3D/Cube等でU/Vのみ使いたいときに便利）。
    戻り値は同じインスタンス（チェーン用に返すだけ）。
    """
    if not isinstance(params, TextureConfigParams):
        raise TypeError("params must be TextureConfigParams")
    if not isinstance(u, AddressMode) or not isinstance(v, AddressMode):
        raise TypeError("u, v must be AddressMode")

    params.address_u = u
    params.address_v = v
    return params

def override_subuv_max_in_game(params: TextureConfigParams, max_in_game: NumericSize) -> TextureConfigParams:
    """
    TextureConfigParams の max_in_game を“破壊的（in-place）”に上書きします。
    戻り値は同じインスタンス（チェーン用に返すだけ）。
    """
    if not isinstance(params, TextureConfigParams):
        raise TypeError("params must be TextureConfigParams")
    
    params.max_in_game = TextureConfigParams._size_to_int(max_in_game)
    return params