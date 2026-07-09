"""tests/unit/test_sanitize.py -- sanitize_component / sanitize_filename のテスト.

Requirements 5.4, 5.5, 5.6 をカバーする。
"""

import pytest

from scanner_rename.domain.sanitize import (
    MAX_FILENAME_LENGTH,
    sanitize_component,
    sanitize_filename,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConstants:
    """MAX_FILENAME_LENGTH の値を検証する."""

    def test_max_filename_length_is_200(self) -> None:
        """上限長は 200 文字."""
        assert MAX_FILENAME_LENGTH == 200


# ---------------------------------------------------------------------------
# sanitize_component -- 1 コンポーネントの整形 (Req 5.4, 5.5)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSanitizeComponentForbiddenChars:
    """禁止文字を _ に置換する (Req 5.4)."""

    @pytest.mark.parametrize(
        ("char", "label"),
        [
            ("/", "slash"),
            ("\\", "backslash"),
            (":", "colon"),
            ("*", "asterisk"),
            ("?", "question"),
            ('"', "double-quote"),
            ("<", "less-than"),
            (">", "greater-than"),
            ("|", "pipe"),
        ],
        ids=[
            "slash",
            "backslash",
            "colon",
            "asterisk",
            "question",
            "double-quote",
            "less-than",
            "greater-than",
            "pipe",
        ],
    )
    def test_forbidden_char_replaced(self, char: str, label: str) -> None:
        """各禁止文字が _ に置換される."""
        result = sanitize_component(f"abc{char}def")
        assert char not in result
        assert result == "abc_def"

    def test_control_char_u0000_replaced(self) -> None:
        """制御文字 U+0000 が置換される."""
        result = sanitize_component("abc\x00def")
        assert result == "abc_def"

    def test_control_char_u001f_replaced(self) -> None:
        """制御文字 U+001F が置換される."""
        result = sanitize_component("abc\x1fdef")
        assert result == "abc_def"

    def test_control_char_u007f_replaced(self) -> None:
        """制御文字 U+007F (DEL) が置換される."""
        result = sanitize_component("abc\x7fdef")
        assert result == "abc_def"

    def test_multiple_forbidden_chars_collapsed(self) -> None:
        """連続する禁止文字が 1 つの _ に畳まれる."""
        result = sanitize_component("abc:*/def")
        assert result == "abc_def"

    def test_mixed_forbidden_and_underscores_collapsed(self) -> None:
        """禁止文字と既存 _ が混在しても連続 _ は 1 つに畳まれる."""
        result = sanitize_component("abc_:_def")
        assert result == "abc_def"


@pytest.mark.unit
class TestSanitizeComponentTrim:
    """先頭・末尾の空白とピリオドを除去する (Req 5.5)."""

    def test_leading_spaces_removed(self) -> None:
        """先頭の空白を除去する."""
        assert sanitize_component("  hello") == "hello"

    def test_trailing_spaces_removed(self) -> None:
        """末尾の空白を除去する."""
        assert sanitize_component("hello  ") == "hello"

    def test_leading_periods_removed(self) -> None:
        """先頭のピリオドを除去する."""
        assert sanitize_component("..hello") == "hello"

    def test_trailing_periods_removed(self) -> None:
        """末尾のピリオドを除去する."""
        assert sanitize_component("hello..") == "hello"

    def test_mixed_leading_trailing_whitespace_and_periods(self) -> None:
        """先頭・末尾の空白とピリオドが混在しても除去する."""
        assert sanitize_component(" . .hello. . ") == "hello"

    def test_consecutive_underscores_collapsed(self) -> None:
        """連続する _ を 1 つに畳む (Req 5.5)."""
        assert sanitize_component("abc___def") == "abc_def"


@pytest.mark.unit
class TestSanitizeComponentJapanese:
    """日本語（全角）文字が無加工で通る."""

    def test_japanese_full_width_passthrough(self) -> None:
        """全角文字がそのまま保持される."""
        assert sanitize_component("確定申告書") == "確定申告書"

    def test_japanese_with_forbidden_char(self) -> None:
        """日本語を含む文字列でも禁止文字は置換される."""
        assert sanitize_component("確定:申告書") == "確定_申告書"

    def test_japanese_katakana_passthrough(self) -> None:
        """カタカナがそのまま保持される."""
        assert sanitize_component("サンプル") == "サンプル"


@pytest.mark.unit
class TestSanitizeComponentEdgeCases:
    """sanitize_component のエッジケース."""

    def test_empty_string(self) -> None:
        """空文字列は空文字列を返す."""
        assert sanitize_component("") == ""

    def test_only_forbidden_chars(self) -> None:
        """禁止文字のみの文字列は _ 1 つになった後トリムで空になる可能性を確認."""
        result = sanitize_component(":::")
        # 全部置換 → "_" → strip でピリオド/空白は無し → "_" が残るはず
        assert result == "_"

    def test_only_spaces_and_periods(self) -> None:
        """空白とピリオドのみの文字列は空文字列を返す."""
        assert sanitize_component(" .. . ") == ""

    def test_normal_text_unchanged(self) -> None:
        """禁止文字を含まない通常テキストは変更されない."""
        assert sanitize_component("hello_world-123") == "hello_world-123"

    def test_parentheses_preserved(self) -> None:
        """括弧はファイル名で使用するため保持される."""
        assert sanitize_component("20211001(R3)") == "20211001(R3)"


# ---------------------------------------------------------------------------
# sanitize_filename -- ファイル名全体の最終ガード (Req 5.4, 5.5, 5.6)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSanitizeFilenameForbiddenChars:
    """sanitize_filename も禁止文字を置換する (Req 5.4)."""

    def test_forbidden_chars_replaced(self) -> None:
        """ファイル名全体でも禁止文字が置換される."""
        result = sanitize_filename('hello:"world".pdf')
        assert ":" not in result
        assert '"' not in result

    def test_control_chars_replaced(self) -> None:
        """制御文字が置換される."""
        result = sanitize_filename("hello\x00world.pdf")
        assert "\x00" not in result


@pytest.mark.unit
class TestSanitizeFilenameTrim:
    """sanitize_filename のトリム動作 (Req 5.5)."""

    def test_leading_trailing_whitespace_removed(self) -> None:
        """先頭・末尾の空白が除去される."""
        result = sanitize_filename("  hello.pdf  ")
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_leading_trailing_periods_removed(self) -> None:
        """先頭・末尾のピリオドが除去される."""
        result = sanitize_filename("..hello.pdf..")
        # ファイル名全体の先頭・末尾からピリオドを除去するが、
        # 内部のピリオド（拡張子の .）は保持
        assert not result.startswith(".")
        assert not result.endswith(".")

    def test_consecutive_underscores_collapsed(self) -> None:
        """連続する _ が畳まれる."""
        result = sanitize_filename("abc___def.pdf")
        assert "___" not in result


@pytest.mark.unit
class TestSanitizeFilenameIdempotent:
    """sanitize_filename は冪等に動作する (Invariant)."""

    @pytest.mark.parametrize(
        "name",
        [
            "20211001(R3)_2025年分_確定申告書_税務署.pdf",
            'hello:"world".pdf',
            "abc\x00\x1f___def.pdf",
            "  ..test.. .pdf  ",
            "a" * 300 + ".pdf",
            "日本語のファイル名.pdf",
            "normal_file.pdf",
            "",
        ],
        ids=[
            "agreed-format",
            "forbidden-chars",
            "control-chars-underscores",
            "whitespace-periods",
            "very-long",
            "japanese",
            "normal",
            "empty",
        ],
    )
    def test_idempotent(self, name: str) -> None:
        """2 回適用しても結果が変わらない."""
        once = sanitize_filename(name)
        twice = sanitize_filename(once)
        assert once == twice


@pytest.mark.unit
class TestSanitizeFilenameLength:
    """sanitize_filename は MAX_FILENAME_LENGTH (200) 以下を保証する (Req 5.6)."""

    def test_short_filename_unchanged(self) -> None:
        """200 文字以下のファイル名はそのまま返す."""
        name = "short_name.pdf"
        result = sanitize_filename(name)
        assert result == name
        assert len(result) <= MAX_FILENAME_LENGTH

    def test_exactly_200_chars_unchanged(self) -> None:
        """ちょうど 200 文字のファイル名はそのまま返す."""
        # .pdf は 4 文字、残り 196 文字
        name = "a" * 196 + ".pdf"
        assert len(name) == 200
        result = sanitize_filename(name)
        assert result == name
        assert len(result) == 200

    def test_exceeding_200_chars_truncated(self) -> None:
        """200 文字超過時はトランケートされる."""
        name = "a" * 250 + ".pdf"
        assert len(name) > 200
        result = sanitize_filename(name)
        assert len(result) <= MAX_FILENAME_LENGTH

    def test_truncation_preserves_pdf_extension(self) -> None:
        """トランケート後も .pdf 拡張子が保持される."""
        name = "a" * 250 + ".pdf"
        result = sanitize_filename(name)
        assert result.endswith(".pdf")
        assert len(result) <= MAX_FILENAME_LENGTH

    def test_long_japanese_filename_truncated(self) -> None:
        """長い日本語ファイル名もトランケートされる."""
        name = "確定申告書" * 50 + ".pdf"
        assert len(name) > 200
        result = sanitize_filename(name)
        assert len(result) <= MAX_FILENAME_LENGTH
        assert result.endswith(".pdf")

    def test_no_extension_long_truncated(self) -> None:
        """拡張子なしの長いファイル名もトランケートされる."""
        name = "a" * 250
        result = sanitize_filename(name)
        assert len(result) <= MAX_FILENAME_LENGTH


@pytest.mark.unit
class TestSanitizeFilenameJapanese:
    """日本語（全角）文字が無加工で通る."""

    def test_japanese_filename_passthrough(self) -> None:
        """日本語を含むファイル名がそのまま保持される."""
        name = "20211001(R3)_2025年分_確定申告書_税務署.pdf"
        result = sanitize_filename(name)
        assert result == name

    def test_full_width_numbers_passthrough(self) -> None:
        """全角数字がそのまま保持される."""
        name = "１２３.pdf"
        result = sanitize_filename(name)
        assert result == name


@pytest.mark.unit
class TestSanitizeFilenameEdgeCases:
    """sanitize_filename のエッジケース."""

    def test_empty_string(self) -> None:
        """空文字列は空文字列を返す."""
        assert sanitize_filename("") == ""

    def test_only_extension(self) -> None:
        """.pdf のみのファイル名は先頭ピリオド除去後に pdf となる可能性."""
        result = sanitize_filename(".pdf")
        # 先頭ピリオドを除去すると "pdf" になる
        assert "." not in result or result == ".pdf" or result == "pdf"
        # 冪等性を確認
        assert sanitize_filename(result) == result

    def test_postcondition_no_forbidden_chars(self) -> None:
        """Postcondition: 戻り値に禁止文字・制御文字を含まない."""
        forbidden = set('/\\:*?"<>|')
        control = {chr(c) for c in range(0x00, 0x20)} | {chr(0x7F)}
        bad_chars = forbidden | control

        name = "".join(chr(c) for c in range(128)) + ".pdf"
        result = sanitize_filename(name)
        for ch in result:
            assert ch not in bad_chars, f"Found forbidden char: {ch!r}"
