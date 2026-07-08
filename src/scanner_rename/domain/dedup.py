"""既存ファイル名一覧に対する重複サフィックス解決.

呼び出し側が渡す既存ファイル名一覧に対し、同名が存在する場合は
拡張子直前に ``_2``, ``_3``, ... と最小の未使用番号を挿入する。
同名が存在しない場合は候補名をそのまま返す。
"""

from collections.abc import Collection


def resolve_duplicate(candidate: str, existing_names: Collection[str]) -> str:
    """候補ファイル名の重複を解決する.

    Preconditions:
        ``candidate`` は拡張子 ``.pdf`` を持つサニタイズ済みファイル名。
    Postconditions:
        戻り値は ``existing_names`` に含まれない。
        ``candidate`` 自体が未使用ならそのまま返す。
    Invariants:
        サフィックス番号は 2 から開始し、最小の未使用番号を返す（決定的）。
        比較は完全一致（大文字小文字を区別）。
    """
    if candidate not in existing_names:
        return candidate

    stem, ext = _split_extension(candidate)
    lookup = (
        set(existing_names)
        if not isinstance(existing_names, (set, frozenset))
        else existing_names
    )

    n = 2
    while True:
        numbered = f"{stem}_{n}{ext}"
        if numbered not in lookup:
            return numbered
        n += 1


def _split_extension(filename: str) -> tuple[str, str]:
    """ファイル名をステム部分と拡張子に分割する.

    ``.pdf`` を持つことを前提とするが、一般的な最後の ``.`` での分割を行う。
    """
    dot_pos = filename.rfind(".")
    if dot_pos == -1:
        return filename, ""
    return filename[:dot_pos], filename[dot_pos:]
