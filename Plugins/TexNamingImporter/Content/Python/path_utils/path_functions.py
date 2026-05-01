import os
from typing import List, Sequence


def _path_stem_tokens(src_path: str) -> List[str]:
    base = os.path.basename(str(src_path).replace("\\", "/"))
    stem, _ext = os.path.splitext(base)
    if not stem:
        return []
    return [t for t in stem.split('_') if t != '']


def has_trailing_suffix_token(src_path: str, suffix: str) -> bool:
    """
    与えられたパスのファイル名末尾トークンが suffix と一致するかを返す。

    Unreal のオブジェクトパス（例: /Game/T_Name_manual.T_Name_manual）でも、
    拡張子扱いになる .ObjectName を除いた左側の名前で判定する。
    """
    tokens = _path_stem_tokens(src_path)
    return bool(tokens and tokens[-1] == suffix)

def collect_suffixes_from_path(src_path: str, suffix_array: Sequence[str]) -> (List[str], List[str]):
    """
    与えられたパスのファイル名から、末尾側に連続して並ぶサフィックス群を抽出して返す。

    戻り値: (見つかったサフィックスのリスト, トークン全体のリスト)

    仕様:
      - 区切りは '_'（アンダースコア）。
      - 最後の拡張子のみ除去して評価（例: 'a.tar.gz' -> 'a.tar'）。
      - 右端から走査し、suffix_array に含まれないトークンが出た時点で打ち切り。
      - 返却順は左→右（自然順）。該当なしなら空配列。

    例:
      'P0_P1_Name_S0_S1_S2.png' と suffix_array=['S0','S1','S2'] -> ['S0','S1','S2']
      'Name_S0_S1.png' と suffix_array=['S0','S1'] -> ['S0','S1']
      'Name_01_S0.png' と suffix_array=['S0'] -> []  # 末尾の直前が '01' のため打ち切り

    注意:
      - 大文字小文字は区別する（厳密一致）。必要なら呼び出し側で揃えてください。
    """
    if not suffix_array:
        return ([],[])

    suffix_set = set(suffix_array)

    tokens = _path_stem_tokens(src_path)
    if not tokens:
        return ([],[])

    collected_rev: List[str] = []
    for tok in reversed(tokens):
        if tok in suffix_set:
            collected_rev.append(tok)
        else:
            break

    if not collected_rev:
        return ([],[])

    return (list(reversed(collected_rev)), tokens)

