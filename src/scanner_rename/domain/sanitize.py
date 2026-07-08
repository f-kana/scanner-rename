"""ファイル名として安全な文字列への整形.

置換対象: ``/ \\ : * ? " < > |`` と制御文字（U+0000--U+001F, U+007F）
→ ``_`` に置換。置換により連続した ``_`` は 1 つに畳む。
先頭・末尾の空白とピリオドを除去する。
上限長は 200 文字（``.pdf`` 込み）。
"""

import re

MAX_FILENAME_LENGTH: int = 200
"""ファイル名の上限長（拡張子を含む）."""

# 禁止文字: / \ : * ? " < > | と制御文字 (U+0000-U+001F, U+007F)
_FORBIDDEN_RE = re.compile(r'[/\\:*?"<>|\x00-\x1f\x7f]')

# 連続するアンダースコア
_CONSECUTIVE_UNDERSCORES_RE = re.compile(r"_{2,}")


def sanitize_component(text: str) -> str:
    """1 コンポーネント（区切り ``_`` を含まない部分）の整形.

    禁止文字を ``_`` に置換し、連続する ``_`` を 1 つに畳み、
    先頭・末尾の空白とピリオドを除去する。
    日本語（全角）文字は無加工で通す。
    """
    result = _replace_forbidden(text)
    result = _collapse_underscores(result)
    result = _strip_edges(result)
    return result


def sanitize_filename(name: str) -> str:
    """ファイル名全体の最終ガード.

    禁止文字を置換し、連続する ``_`` を畳み、先頭・末尾の空白と
    ピリオドを除去し、上限長（200 文字）を超過する場合はトランケートする。

    Postconditions:
        - 戻り値に禁止文字・制御文字を含まない
        - 戻り値は ``MAX_FILENAME_LENGTH`` 以下
    Invariants:
        - 冪等（``sanitize_filename(sanitize_filename(x)) == sanitize_filename(x)``）
    """
    result = _replace_forbidden(name)
    result = _collapse_underscores(result)
    result = _strip_edges(result)
    result = _enforce_length(result)
    return result


# --- private helpers (呼び出し先) ---


def _replace_forbidden(text: str) -> str:
    """禁止文字・制御文字を ``_`` に置換する."""
    return _FORBIDDEN_RE.sub("_", text)


def _collapse_underscores(text: str) -> str:
    """連続するアンダースコアを 1 つに畳む."""
    return _CONSECUTIVE_UNDERSCORES_RE.sub("_", text)


def _strip_edges(text: str) -> str:
    """先頭・末尾の空白とピリオドを除去する."""
    return text.strip(" .")


def _enforce_length(text: str) -> str:
    """上限長を超過する場合にトランケートする.

    ``.pdf`` 拡張子を持つ場合は拡張子を保持してステム部分を切り詰める。
    拡張子なしの場合は単純にトランケートする。
    トランケート後の末尾の空白・ピリオド・アンダースコアも除去する。
    """
    if len(text) <= MAX_FILENAME_LENGTH:
        return text

    if text.endswith(".pdf"):
        ext = ".pdf"
        max_stem = MAX_FILENAME_LENGTH - len(ext)
        stem = text[: -len(ext)]
        stem = stem[:max_stem].rstrip(" ._")
        return stem + ext
    else:
        return text[:MAX_FILENAME_LENGTH].rstrip(" ._")
