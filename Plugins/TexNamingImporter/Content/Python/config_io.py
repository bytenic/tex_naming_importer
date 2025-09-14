import json
from pathlib import Path
from typing import Dict, Optional, Any, Union

from type_define import (
    TextureConfigParams,
    AddressMode,
    CompressionKind,
    SRGBMode,
    SizePreset,
    NumericSize,
)

# ---------- 単一 params のシリアライズ / デシリアライズ ----------

def _params_to_dict(p: TextureConfigParams, *, minimal: bool = True) -> Dict[str, Any]:
    """
    TextureConfigParams -> dict（JSON化しやすいフラット構造）
    Enumは .name、max_in_gameは整数（0=無制限）に正規化します。
    minimal=True のとき None の項目は出力しません。
    """
    def _enum_name(e: Optional[object]) -> Optional[str]:
        return None if e is None else e.name

    def _size_to_int(v: Optional[NumericSize]) -> Optional[int]:
        if v is None:
            return None
        if isinstance(v, SizePreset):
            return int(v)
        if isinstance(v, int):
            return max(0, v)
        raise TypeError("max_in_game must be int or SizePreset")

    out = {
        "address_u": _enum_name(p.address_u),
        "address_v": _enum_name(p.address_v),
        "address_z": _enum_name(p.address_z),
        "max_in_game": _size_to_int(p.max_in_game),
        "enforce_pow2": bool(p.enforce_pow2) if p.max_in_game is not None else None,
        "compression": _enum_name(p.compression),
        "srgb": _enum_name(p.srgb),
        "save": bool(p.save),
        "silent": bool(p.silent),
    }
    if minimal:
        return {k: v for k, v in out.items() if v is not None}
    return out


def _params_from_dict(d: Dict[str, Any]) -> TextureConfigParams:
    """
    dict -> TextureConfigParams
    各Enumは .name 文字列（大文字そのまま）を期待します。
    max_in_game は整数（0=無制限）。未知キーは無視します。
    """
    def _enum(enum_cls, name: Optional[Union[str, int]]):
        if name is None:
            return None
        if isinstance(name, int):  # 誤って数値で入っていた場合も許容
            # Int値 -> メンバーを総当たりで検索
            for m in enum_cls:
                if getattr(m, "value", None) == name:
                    return m
            raise ValueError(f"unknown {enum_cls.__name__} int: {name}")
        if isinstance(name, str):
            name = name.strip()
            try:
                return enum_cls[name]
            except KeyError:
                raise ValueError(f"unknown {enum_cls.__name__} name: {name}")
        raise TypeError(f"{enum_cls.__name__} must be enum name string")

    def _size(v: Optional[Union[int, str]]) -> Optional[int]:
        if v is None:
            return None
        if isinstance(v, int):
            return max(0, v)
        if isinstance(v, str):
            v = v.strip()
            # 互換性: "AUTO" / "P2048" を許容して整数化（保存側は原則 int）
            if v.upper() == "AUTO":
                return 0
            if v.upper().startswith("P") and v[1:].isdigit():
                return max(0, int(v[1:]))
            if v.isdigit():
                return max(0, int(v))
        raise ValueError("max_in_game must be int (0=auto) or 'AUTO'/'P####'")

    max_px = _size(d.get("max_in_game"))

    return TextureConfigParams(
        address_u=_enum(AddressMode, d.get("address_u")),
        address_v=_enum(AddressMode, d.get("address_v")),
        address_z=_enum(AddressMode, d.get("address_z")),
        max_in_game=max_px if max_px is None else max_px,  # int（0=無制限）
        enforce_pow2=bool(d.get("enforce_pow2", False)),
        compression=_enum(CompressionKind, d.get("compression")),
        srgb=_enum(SRGBMode, d.get("srgb")),
        save=bool(d.get("save", True)),
        silent=bool(d.get("silent", False)),
    )

# ---------- 保存 / 読込 ----------

def save_params_map_json(file_path: Union[str, Path], params_map: Dict[str, TextureConfigParams], *,
                        indent: int = 2, ensure_ascii: bool = False, minimal: bool = True) -> None:
    """
    {"col": TextureConfigParams, "msk": ..., ...} を JSON で保存します。
    """
    path = Path(file_path)
    payload = {key: _params_to_dict(p, minimal=minimal) for key, p in params_map.items()}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=indent, ensure_ascii=ensure_ascii)


def load_params_map_json(file_path: Union[str, Path]) -> Dict[str, TextureConfigParams]:
    """
    JSON から {"col": TextureConfigParams, ...} を復元します。
    余計なキーは無視します。各項目の欠落は None/既定値として復元します。
    """
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        raise ValueError("root must be an object mapping keys to TextureConfigParams dicts")

    out: Dict[str, TextureConfigParams] = {}
    for key, val in raw.items():
        if not isinstance(val, dict):
            raise ValueError(f"value for key '{key}' must be an object")
        out[key] = _params_from_dict(val)
    return out