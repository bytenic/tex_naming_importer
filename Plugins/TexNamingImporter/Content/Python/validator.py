from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, List, Optional, Iterable

@dataclass
class SuffixValidationResult:
    ok: bool
    # 行インデックス → 実際に一致したサフィックス（元の大小保持）
    matches_by_row: List[Optional[str]] = None
    # 失敗時の情報
    error: Optional[str] = None
    # 失敗した行（カテゴリ）インデックス。0 が先頭行（＝ suffix_index の先頭）
    failed_row_index: Optional[int] = None
    # 解析に使った元配列
    suffix_list: Optional[List[str]] = None


def validate_suffixes(
    suffix_list: List[str],
    suffix_grid: List[List[str]],
) -> SuffixValidationResult:
    """
    Suffix命名規則の検証を行う:
      - suffix_list はサフィックスのみ（テクスチャ名等は含まれない）
      - 行数（=カテゴリ数）とサフィックス数が一致しない場合は即エラー
      - 行 i の許容キー群 (suffix_grid[i]) に対して suffix_list[i] を大小無視で照合
      - すべて一致で OK、どこか1つでも不一致なら即 NG
    """
    # 行数（カテゴリ数）とサフィックス数の厳密一致を要求
    if len(suffix_list) != len(suffix_grid):
        return SuffixValidationResult(
            ok=False,
            error=f"サフィックス数と規則行数が一致しません。expected={len(suffix_grid)}, actual={len(suffix_list)}",
            failed_row_index=None,
            suffix_list=suffix_list,
        )

    # 各行 i について、suffix_list[i] が suffix_grid[i] の許容キーに含まれるか検証
    for i, (token_orig, allowed_row) in enumerate(zip(suffix_list, suffix_grid)):
        token_l = token_orig.lower()
        allowed_lower = {k.lower() for k in allowed_row or []}
        if token_l not in allowed_lower:
            preview = ", ".join(list(allowed_lower)[:8]) + ("..." if len(allowed_lower) > 8 else "")
            return SuffixValidationResult(
                ok=False,
                error=f"行 {i} のサフィックス '{token_orig}' は許容値に含まれていません。許容例: [{preview}]",
                failed_row_index=i,
                suffix_list=suffix_list,
            )

    # すべて一致
    return SuffixValidationResult(
        ok=True,
        matches_by_row=list(suffix_list),
        suffix_list=suffix_list,
    )


def _normalize_unreal_path(p: str) -> str:
    """
    Unreal の仮想パスを簡易正規化:
      - バックスラッシュ -> スラッシュ
      - 連続スラッシュを1つに
      - 末尾スラッシュを除去（ただし "/" はそのまま）
      - 前後の空白除去
    """
    if p is None:
        return ""
    s = str(p).strip().replace("\\", "/")
    # 連続スラッシュを1つに
    while "//" in s:
        s = s.replace("//", "/")
    # 末尾スラッシュ除去（ルート除く）
    if len(s) > 1 and s.endswith("/"):
        s = s[:-1]
    return s


def _extract_dir_from_asset_path(asset_path: str) -> str:
    """
    アセットパスからディレクトリ部分を取り出す。
    例:
      '/Game/VFX/Smoke/T_Smoke.T_Smoke' -> '/Game/VFX/Smoke'
      '/Game/VFX/Smoke/'               -> '/Game/VFX/Smoke'
      '/Game/VFX'                      -> '/Game'  (最後に '/' が無ければ最終コンポーネントをファイルとみなす)
    """
    s = _normalize_unreal_path(asset_path)
    if not s:
        return ""

    # 末尾に .ObjectName が付いていても、ディレクトリ抽出には無関係なので
    # 単純に最後の '/' までをディレクトリとして扱う
    if s.endswith("/"):
        # 末尾がディレクトリ表現だった場合、すでに _normalize で除去済のためここには来ない想定
        pass

    last_slash = s.rfind("/")
    if last_slash <= 0:
        # '/Name' または 'Name' のようなケース
        return "/" if s.startswith("/") else ""
    # ディレクトリ部分（最後の '/' より前）
    return s[:last_slash]


def _is_under_dir(path_dir: str, allowed_dir: str) -> bool:
    """
    ディレクトリ境界を考慮して path_dir が allowed_dir 配下かどうかを判定。
    同一ディレクトリも True。
    """
    pd = _normalize_unreal_path(path_dir)
    ad = _normalize_unreal_path(allowed_dir)

    if not pd or not ad:
        return False

    if pd == ad:
        return True
    # 境界を厳密にするため、allowed の末尾に '/' を付けて startswith を見る
    return pd.startswith(ad + "/")


def validate_directory(asset_path: str, allowed_dirs: Iterable[str]) -> bool:
    """
    第一引数のテクスチャ（アセット）パスが、第二引数のいずれかのディレクトリ配下にあるか判定する。

    Args:
        asset_path: '/Game/...' 形式のアセットパスを想定（例: '/Game/VFX/Smoke/T_Smoke.T_Smoke'）
        allowed_dirs: 許容ディレクトリの配列（例: ['/Game/VFX', '/Game/Characters']）

    Returns:
        bool: いずれかの許容ディレクトリの「直下または配下」にあれば True、そうでなければ False
    """
    if not asset_path:
        return False
    path_dir = _extract_dir_from_asset_path(asset_path)
    if not path_dir:
        return False

    for d in allowed_dirs or []:
        if _is_under_dir(path_dir, d):
            return True
    return False


def regex_any_match(pattern: str, candidates: List[str]) -> bool:
    '''
    第1引数の正規表現パターンに対して、第2引数の文字列リストのいずれかがマッチするかを判定します。
      - マッチが1つでもあれば True
      - 1つもマッチしなければ False
      - パターンが不正（re.error）の場合は False
    ここでの「マッチ」は re.search（部分一致）です。完全一致は ^ と $ を使ってください。
    '''
    if not pattern or not candidates:
        return False
    try:
        reg = re.compile(pattern)
    except re.error:
        return False
    for s in candidates:
        if s is None:
            continue
        if reg.search(str(s)):
            return True
    return False