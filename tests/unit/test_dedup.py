"""tests/unit/test_dedup.py -- resolve_duplicate のテスト.

Requirements 5.1, 5.2, 5.3 をカバーする。
initial-context.md の重複例（_2, _3 の連番）を再現する。
"""

import pytest

from scanner_rename.domain.dedup import resolve_duplicate

# ---------------------------------------------------------------------------
# Req 5.3: 既存一覧に存在しない場合はそのまま返す
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestResolveDuplicateNoConflict:
    """候補名が既存一覧に存在しない場合はそのまま返す (Req 5.3)."""

    def test_no_existing_names(self) -> None:
        """既存名一覧が空のとき、候補名をそのまま返す."""
        result = resolve_duplicate("report.pdf", [])
        assert result == "report.pdf"

    def test_candidate_not_in_existing(self) -> None:
        """候補名が既存一覧に含まれないとき、そのまま返す."""
        result = resolve_duplicate(
            "report.pdf",
            ["other.pdf", "another.pdf"],
        )
        assert result == "report.pdf"

    def test_candidate_not_in_existing_set(self) -> None:
        """既存名一覧が set でも動作する."""
        result = resolve_duplicate(
            "report.pdf",
            {"other.pdf", "another.pdf"},
        )
        assert result == "report.pdf"


# ---------------------------------------------------------------------------
# Req 5.1: 同名が存在する場合は _2 を挿入
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestResolveDuplicateFirstConflict:
    """同名が存在する場合は _2 を挿入する (Req 5.1)."""

    def test_first_duplicate_gets_suffix_2(self) -> None:
        """最初の重複で _2 が挿入される."""
        result = resolve_duplicate(
            "report.pdf",
            ["report.pdf"],
        )
        assert result == "report_2.pdf"

    def test_suffix_before_extension(self) -> None:
        """サフィックスは拡張子の直前に挿入される."""
        result = resolve_duplicate(
            "20211001(R3)_住宅取得資金に係る借入金の年末残高等証明書.pdf",
            ["20211001(R3)_住宅取得資金に係る借入金の年末残高等証明書.pdf"],
        )
        assert result == "20211001(R3)_住宅取得資金に係る借入金の年末残高等証明書_2.pdf"


# ---------------------------------------------------------------------------
# Req 5.2: _2 も存在する場合は _3, _4 と増やす
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestResolveDuplicateSequentialConflicts:
    """_2 も存在する場合は番号を増やし、未使用の最小番号を返す (Req 5.2)."""

    def test_second_duplicate_gets_suffix_3(self) -> None:
        """_2 も存在するとき _3 が返される."""
        result = resolve_duplicate(
            "report.pdf",
            ["report.pdf", "report_2.pdf"],
        )
        assert result == "report_3.pdf"

    def test_third_duplicate_gets_suffix_4(self) -> None:
        """_2 と _3 も存在するとき _4 が返される."""
        result = resolve_duplicate(
            "report.pdf",
            ["report.pdf", "report_2.pdf", "report_3.pdf"],
        )
        assert result == "report_4.pdf"

    def test_gap_in_sequence_uses_smallest(self) -> None:
        """番号に欠番がある場合は最小の未使用番号を返す."""
        result = resolve_duplicate(
            "report.pdf",
            ["report.pdf", "report_2.pdf", "report_4.pdf"],
        )
        assert result == "report_3.pdf"


# ---------------------------------------------------------------------------
# initial-context.md の重複例を再現
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestResolveDuplicateInitialContextExample:
    """initial-context.md の重複例を再現する.

    例:
    20211001(R3)_住宅取得資金に係る借入金の年末残高等証明書.pdf
    20211001(R3)_住宅取得資金に係る借入金の年末残高等証明書_2.pdf
    20211001(R3)_住宅取得資金に係る借入金の年末残高等証明書_3.pdf
    """

    BASE = "20211001(R3)_住宅取得資金に係る借入金の年末残高等証明書"

    def test_first_file_no_suffix(self) -> None:
        """最初のファイルはサフィックスなし."""
        result = resolve_duplicate(f"{self.BASE}.pdf", [])
        assert result == f"{self.BASE}.pdf"

    def test_second_file_gets_suffix_2(self) -> None:
        """2 番目のファイルは _2 が付く."""
        existing = [f"{self.BASE}.pdf"]
        result = resolve_duplicate(f"{self.BASE}.pdf", existing)
        assert result == f"{self.BASE}_2.pdf"

    def test_third_file_gets_suffix_3(self) -> None:
        """3 番目のファイルは _3 が付く."""
        existing = [
            f"{self.BASE}.pdf",
            f"{self.BASE}_2.pdf",
        ]
        result = resolve_duplicate(f"{self.BASE}.pdf", existing)
        assert result == f"{self.BASE}_3.pdf"

    def test_full_sequence(self) -> None:
        """3 ファイルの連番を順に resolve して再現する."""
        existing: list[str] = []
        results: list[str] = []

        for _ in range(3):
            name = resolve_duplicate(f"{self.BASE}.pdf", existing)
            results.append(name)
            existing.append(name)

        assert results == [
            f"{self.BASE}.pdf",
            f"{self.BASE}_2.pdf",
            f"{self.BASE}_3.pdf",
        ]


# ---------------------------------------------------------------------------
# 大文字小文字の区別（完全一致）
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestResolveDuplicateCaseSensitive:
    """比較は完全一致（大文字小文字を区別）."""

    def test_different_case_not_conflict(self) -> None:
        """大文字小文字が異なれば重複とみなさない."""
        result = resolve_duplicate(
            "Report.pdf",
            ["report.pdf"],
        )
        assert result == "Report.pdf"


# ---------------------------------------------------------------------------
# エッジケース
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestResolveDuplicateEdgeCases:
    """resolve_duplicate のエッジケース."""

    def test_many_duplicates(self) -> None:
        """多数の重複が存在する場合でも正しく動作する."""
        base = "doc"
        existing = [f"{base}.pdf"] + [f"{base}_{i}.pdf" for i in range(2, 101)]
        result = resolve_duplicate(f"{base}.pdf", existing)
        assert result == f"{base}_101.pdf"

    def test_existing_as_tuple(self) -> None:
        """既存名一覧が tuple でも動作する."""
        result = resolve_duplicate(
            "report.pdf",
            ("report.pdf", "report_2.pdf"),
        )
        assert result == "report_3.pdf"

    def test_existing_as_frozenset(self) -> None:
        """既存名一覧が frozenset でも動作する."""
        result = resolve_duplicate(
            "report.pdf",
            frozenset({"report.pdf", "report_2.pdf"}),
        )
        assert result == "report_3.pdf"
