"""tests/unit/test_naming.py -- 命名入力の契約型・入力検証・ファイル名組み立てのテスト.

Requirement 4.1-4.9 をカバーする。
Task 6.1: 型の不変性（frozen）と入力不備ケースの unit テスト。
Task 6.2: build_filename によるファイル名組み立てテスト。
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from scanner_rename.domain.errors import NamingInputError
from scanner_rename.domain.naming import (
    NamingInput,
    Period,
    PeriodKind,
    YearMonth,
    build_filename,
    validate_naming_input,
)
from scanner_rename.domain.sanitize import MAX_FILENAME_LENGTH
from scanner_rename.domain.scanner_filename import ScannerFilename


def _make_scanner(ts: datetime | None = None) -> ScannerFilename:
    """テスト用のデフォルトスキャナーファイル名を生成する."""
    if ts is None:
        ts = datetime(2026, 5, 7, 13, 27, 42)
    return ScannerFilename(scan_timestamp=ts, sequence=1)


# ---------------------------------------------------------------------------
# YearMonth: frozen 不変性
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Period: オプションフィールドのデフォルト値
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestPeriodFrozen:
    """Period のオプションフィールドのデフォルト値を検証する."""

    def test_defaults_are_none(self) -> None:
        """デフォルト値は None である."""
        period = Period(kind=PeriodKind.CALENDAR_YEAR)
        assert period.year is None
        assert period.start is None
        assert period.end is None


# ---------------------------------------------------------------------------
# PeriodKind: メンバー数ガード
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestPeriodKindEnum:
    """PeriodKind のメンバー数が設計通りであることをガードする."""

    def test_member_count(self) -> None:
        """PeriodKind は 3 メンバーのみ."""
        assert len(PeriodKind) == 3


# ---------------------------------------------------------------------------
# validate_naming_input: タイトル空・空白のみ → NamingInputError
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestValidateNamingInputTitleErrors:
    """タイトルが空・空白のみなら NamingInputError (Req 4.8)."""

    @pytest.mark.parametrize(
        ("title", "reason"),
        [
            ("", "empty-string"),
            ("   ", "whitespace-only-spaces"),
            ("\t", "whitespace-only-tab"),
            ("\n", "whitespace-only-newline"),
            ("  \t\n  ", "whitespace-mixed"),
        ],
        ids=[
            "empty-string",
            "whitespace-only-spaces",
            "whitespace-only-tab",
            "whitespace-only-newline",
            "whitespace-mixed",
        ],
    )
    def test_empty_or_whitespace_title_raises(self, title: str, reason: str) -> None:
        """空・空白のみのタイトルは NamingInputError を送出する."""
        ni = NamingInput(
            title=title,
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=None,
            issuer=None,
        )
        with pytest.raises(NamingInputError, match="title"):
            validate_naming_input(ni)

    def test_valid_title_no_error(self) -> None:
        """有効なタイトルではエラーを送出しない."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=None,
            issuer=None,
        )
        validate_naming_input(ni)  # 例外なし


# ---------------------------------------------------------------------------
# validate_naming_input: Period 必須フィールド欠落 → NamingInputError
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestValidateNamingInputPeriodErrors:
    """Period の必須フィールド欠落は NamingInputError (Req 4.8)."""

    def test_calendar_year_missing_year(self) -> None:
        """CALENDAR_YEAR で year が None なら NamingInputError."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=Period(kind=PeriodKind.CALENDAR_YEAR, year=None),
            issuer=None,
        )
        with pytest.raises(NamingInputError, match="year"):
            validate_naming_input(ni)

    def test_fiscal_year_missing_year(self) -> None:
        """FISCAL_YEAR で year が None なら NamingInputError."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=Period(
                kind=PeriodKind.FISCAL_YEAR,
                year=None,
                start=YearMonth(year=2025, month=4),
                end=YearMonth(year=2026, month=3),
            ),
            issuer=None,
        )
        with pytest.raises(NamingInputError, match="year"):
            validate_naming_input(ni)

    def test_fiscal_year_missing_start(self) -> None:
        """FISCAL_YEAR で start が None なら NamingInputError."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=Period(
                kind=PeriodKind.FISCAL_YEAR,
                year=2025,
                start=None,
                end=YearMonth(year=2026, month=3),
            ),
            issuer=None,
        )
        with pytest.raises(NamingInputError, match="start"):
            validate_naming_input(ni)

    def test_fiscal_year_missing_end(self) -> None:
        """FISCAL_YEAR で end が None なら NamingInputError."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=Period(
                kind=PeriodKind.FISCAL_YEAR,
                year=2025,
                start=YearMonth(year=2025, month=4),
                end=None,
            ),
            issuer=None,
        )
        with pytest.raises(NamingInputError, match="end"):
            validate_naming_input(ni)

    def test_explicit_range_missing_start(self) -> None:
        """EXPLICIT_RANGE で start が None なら NamingInputError."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=Period(
                kind=PeriodKind.EXPLICIT_RANGE,
                start=None,
                end=YearMonth(year=2026, month=3),
            ),
            issuer=None,
        )
        with pytest.raises(NamingInputError, match="start"):
            validate_naming_input(ni)

    def test_explicit_range_missing_end(self) -> None:
        """EXPLICIT_RANGE で end が None なら NamingInputError."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=Period(
                kind=PeriodKind.EXPLICIT_RANGE,
                start=YearMonth(year=2025, month=4),
                end=None,
            ),
            issuer=None,
        )
        with pytest.raises(NamingInputError, match="end"):
            validate_naming_input(ni)

    def test_explicit_range_missing_both(self) -> None:
        """EXPLICIT_RANGE で start/end 両方 None なら NamingInputError."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=Period(kind=PeriodKind.EXPLICIT_RANGE),
            issuer=None,
        )
        with pytest.raises(NamingInputError):
            validate_naming_input(ni)


# ---------------------------------------------------------------------------
# validate_naming_input: 正常系（エラーなし）
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestValidateNamingInputValid:
    """正しい入力ではエラーを送出しない."""

    def test_no_period(self) -> None:
        """期間なしの入力は有効."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=None,
            issuer=None,
        )
        validate_naming_input(ni)

    def test_calendar_year_valid(self) -> None:
        """CALENDAR_YEAR で year 指定ありは有効."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=Period(kind=PeriodKind.CALENDAR_YEAR, year=2024),
            issuer=None,
        )
        validate_naming_input(ni)

    def test_fiscal_year_valid(self) -> None:
        """FISCAL_YEAR で year/start/end 全指定ありは有効."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=Period(
                kind=PeriodKind.FISCAL_YEAR,
                year=2025,
                start=YearMonth(year=2025, month=4),
                end=YearMonth(year=2026, month=3),
            ),
            issuer=None,
        )
        validate_naming_input(ni)

    def test_explicit_range_valid(self) -> None:
        """EXPLICIT_RANGE で start/end 指定ありは有効."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=Period(
                kind=PeriodKind.EXPLICIT_RANGE,
                start=YearMonth(year=2025, month=1),
                end=YearMonth(year=2025, month=6),
            ),
            issuer=None,
        )
        validate_naming_input(ni)

    def test_with_all_fields(self) -> None:
        """全フィールド指定の入力は有効."""
        ni = NamingInput(
            title="住宅ローン年末残高証明書",
            document_date=date(2021, 10, 1),
            date_has_era=True,
            period=Period(kind=PeriodKind.CALENDAR_YEAR, year=2025),
            issuer="三井住友銀行",
        )
        validate_naming_input(ni)

    def test_document_date_none_is_valid(self) -> None:
        """document_date が None でも有効（フォールバック用）."""
        ni = NamingInput(
            title="領収書",
            document_date=None,
            date_has_era=False,
            period=None,
            issuer=None,
        )
        validate_naming_input(ni)

    def test_issuer_empty_string_is_valid(self) -> None:
        """issuer が空文字列でもバリデーションは通る（命名時に別途処理）."""
        ni = NamingInput(
            title="領収書",
            document_date=date(2025, 1, 1),
            date_has_era=False,
            period=None,
            issuer="",
        )
        validate_naming_input(ni)


# ---------------------------------------------------------------------------
# validate_naming_input: エラーメッセージの内容確認
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestValidateNamingInputErrorMessages:
    """エラーメッセージが診断可能な内容を含む."""

    def test_title_error_message_contains_field_name(self) -> None:
        """タイトルエラーのメッセージに 'title' が含まれる."""
        ni = NamingInput(
            title="",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=None,
            issuer=None,
        )
        with pytest.raises(NamingInputError, match="title"):
            validate_naming_input(ni)

    def test_period_year_error_message_contains_field_name(self) -> None:
        """期間 year エラーのメッセージに 'year' が含まれる."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=Period(kind=PeriodKind.CALENDAR_YEAR, year=None),
            issuer=None,
        )
        with pytest.raises(NamingInputError, match="year"):
            validate_naming_input(ni)

    def test_period_start_error_message_contains_field_name(self) -> None:
        """期間 start エラーのメッセージに 'start' が含まれる."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=Period(
                kind=PeriodKind.EXPLICIT_RANGE,
                start=None,
                end=YearMonth(year=2026, month=3),
            ),
            issuer=None,
        )
        with pytest.raises(NamingInputError, match="start"):
            validate_naming_input(ni)


# ===========================================================================
# build_filename テスト (Task 6.2)
# ===========================================================================


# ---------------------------------------------------------------------------
# 合意例 3 件の完全一致再現 (Req 4.1, 4.2, 4.3)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestBuildFilenameAgreedExamples:
    """initial-context.md の合意例 3 件の完全一致再現."""

    def test_housing_loan_certificate(self) -> None:
        """住宅ローン証明書: 元号表記 + 発行元あり + 期間なし."""
        ni = NamingInput(
            title="住宅取得資金に係る借入金の年末残高等証明書",
            document_date=date(2021, 10, 1),
            date_has_era=True,
            period=None,
            issuer="三井住友銀行",
        )
        result = build_filename(ni, _make_scanner())
        expected = (
            "20211001(R3)_住宅取得資金に係る借入金の年末残高等証明書_三井住友銀行.pdf"
        )
        assert result == expected

    def test_tax_return_first_table(self) -> None:
        """確定申告書第一表: 元号表記 + 年分あり + 発行元なし."""
        ni = NamingInput(
            title="確定申告書第一表",
            document_date=date(2026, 3, 10),
            date_has_era=True,
            period=Period(kind=PeriodKind.CALENDAR_YEAR, year=2025),
            issuer=None,
        )
        result = build_filename(ni, _make_scanner())
        assert result == "20260310(R8)_2025年分_確定申告書第一表.pdf"

    def test_medical_expense_notice(self) -> None:
        """医療費通知: 元号表記 + 年度分あり + 発行元なし."""
        ni = NamingInput(
            title="医療費通知",
            document_date=date(2026, 4, 15),
            date_has_era=True,
            period=Period(
                kind=PeriodKind.FISCAL_YEAR,
                year=2025,
                start=YearMonth(year=2025, month=4),
                end=YearMonth(year=2026, month=3),
            ),
            issuer=None,
        )
        result = build_filename(ni, _make_scanner())
        assert result == "20260415(R8)_2025年度分(202504-202603)_医療費通知.pdf"


# ---------------------------------------------------------------------------
# 省略規則の組み合わせ (Req 4.5, 4.6)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestBuildFilenameOmissionRules:
    """省略規則の組み合わせ: 期間なし・発行元なしのコンポーネント省略."""

    def test_no_period_no_issuer(self) -> None:
        """期間なし・発行元なし -> 日付_タイトル.pdf."""
        ni = NamingInput(
            title="領収書",
            document_date=date(2025, 6, 1),
            date_has_era=False,
            period=None,
            issuer=None,
        )
        result = build_filename(ni, _make_scanner())
        assert result == "20250601_領収書.pdf"

    def test_no_period_with_issuer(self) -> None:
        """期間なし・発行元あり -> 日付_タイトル_発行元.pdf."""
        ni = NamingInput(
            title="領収書",
            document_date=date(2025, 6, 1),
            date_has_era=False,
            period=None,
            issuer="コンビニ",
        )
        result = build_filename(ni, _make_scanner())
        assert result == "20250601_領収書_コンビニ.pdf"

    def test_with_period_no_issuer(self) -> None:
        """期間あり・発行元なし -> 日付_期間_タイトル.pdf."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2026, 3, 10),
            date_has_era=True,
            period=Period(kind=PeriodKind.CALENDAR_YEAR, year=2025),
            issuer=None,
        )
        result = build_filename(ni, _make_scanner())
        assert result == "20260310(R8)_2025年分_確定申告書.pdf"

    def test_all_components(self) -> None:
        """全コンポーネントあり -> 日付_期間_タイトル_発行元.pdf."""
        ni = NamingInput(
            title="残高証明書",
            document_date=date(2025, 12, 31),
            date_has_era=True,
            period=Period(kind=PeriodKind.CALENDAR_YEAR, year=2025),
            issuer="みずほ銀行",
        )
        result = build_filename(ni, _make_scanner())
        assert result == "20251231(R7)_2025年分_残高証明書_みずほ銀行.pdf"

    def test_issuer_empty_string_omitted(self) -> None:
        """issuer が空文字列なら発行元コンポーネントを省略する."""
        ni = NamingInput(
            title="領収書",
            document_date=date(2025, 6, 1),
            date_has_era=False,
            period=None,
            issuer="",
        )
        result = build_filename(ni, _make_scanner())
        assert result == "20250601_領収書.pdf"

    def test_issuer_whitespace_only_omitted(self) -> None:
        """issuer が空白のみなら発行元コンポーネントを省略する."""
        ni = NamingInput(
            title="領収書",
            document_date=date(2025, 6, 1),
            date_has_era=False,
            period=None,
            issuer="   ",
        )
        result = build_filename(ni, _make_scanner())
        assert result == "20250601_領収書.pdf"


# ---------------------------------------------------------------------------
# 期間フォーマット (Req 4.2, 4.3, 4.4)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestBuildFilenamePeriodFormats:
    """期間コンポーネントの各形式."""

    def test_calendar_year_format(self) -> None:
        """CALENDAR_YEAR -> YYYY年分."""
        ni = NamingInput(
            title="テスト文書",
            document_date=date(2025, 1, 1),
            date_has_era=False,
            period=Period(kind=PeriodKind.CALENDAR_YEAR, year=2024),
            issuer=None,
        )
        result = build_filename(ni, _make_scanner())
        assert result == "20250101_2024年分_テスト文書.pdf"

    def test_fiscal_year_format(self) -> None:
        """FISCAL_YEAR -> YYYY年度分(YYYYMM-YYYYMM)."""
        ni = NamingInput(
            title="テスト文書",
            document_date=date(2025, 1, 1),
            date_has_era=False,
            period=Period(
                kind=PeriodKind.FISCAL_YEAR,
                year=2024,
                start=YearMonth(year=2024, month=4),
                end=YearMonth(year=2025, month=3),
            ),
            issuer=None,
        )
        result = build_filename(ni, _make_scanner())
        assert result == "20250101_2024年度分(202404-202503)_テスト文書.pdf"

    def test_explicit_range_format(self) -> None:
        """EXPLICIT_RANGE -> YYYYMM-YYYYMM."""
        ni = NamingInput(
            title="テスト文書",
            document_date=date(2025, 1, 1),
            date_has_era=False,
            period=Period(
                kind=PeriodKind.EXPLICIT_RANGE,
                start=YearMonth(year=2024, month=7),
                end=YearMonth(year=2025, month=6),
            ),
            issuer=None,
        )
        result = build_filename(ni, _make_scanner())
        assert result == "20250101_202407-202506_テスト文書.pdf"


# ---------------------------------------------------------------------------
# 文書日付フォールバック (Req 4.7)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestBuildFilenameDateFallback:
    """文書日付なし -> スキャンタイムスタンプの日付部分にフォールバック."""

    def test_fallback_to_scan_timestamp(self) -> None:
        """document_date が None のときスキャンタイムスタンプの日付を使う."""
        scanner = ScannerFilename(
            scan_timestamp=datetime(2026, 5, 7, 13, 27, 42),
            sequence=1,
        )
        ni = NamingInput(
            title="領収書",
            document_date=None,
            date_has_era=False,
            period=None,
            issuer=None,
        )
        result = build_filename(ni, scanner)
        assert result == "20260507_領収書.pdf"

    def test_fallback_with_era(self) -> None:
        """date_has_era=True でフォールバックした場合も元号付き."""
        scanner = ScannerFilename(
            scan_timestamp=datetime(2026, 5, 7, 13, 27, 42),
            sequence=1,
        )
        ni = NamingInput(
            title="領収書",
            document_date=None,
            date_has_era=True,
            period=None,
            issuer=None,
        )
        result = build_filename(ni, scanner)
        assert result == "20260507(R8)_領収書.pdf"


# ---------------------------------------------------------------------------
# build_filename の入力不備エラー (Req 4.8)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestBuildFilenameInputErrors:
    """build_filename が validate_naming_input を呼び入力不備を検出する."""

    def test_empty_title_raises(self) -> None:
        """空タイトルは NamingInputError."""
        ni = NamingInput(
            title="",
            document_date=date(2025, 1, 1),
            date_has_era=False,
            period=None,
            issuer=None,
        )
        with pytest.raises(NamingInputError, match="title"):
            build_filename(ni, _make_scanner())

    def test_whitespace_title_raises(self) -> None:
        """空白のみタイトルは NamingInputError."""
        ni = NamingInput(
            title="   ",
            document_date=date(2025, 1, 1),
            date_has_era=False,
            period=None,
            issuer=None,
        )
        with pytest.raises(NamingInputError, match="title"):
            build_filename(ni, _make_scanner())

    def test_invalid_period_raises(self) -> None:
        """Period 必須フィールド欠落は NamingInputError."""
        ni = NamingInput(
            title="テスト",
            document_date=date(2025, 1, 1),
            date_has_era=False,
            period=Period(kind=PeriodKind.CALENDAR_YEAR, year=None),
            issuer=None,
        )
        with pytest.raises(NamingInputError):
            build_filename(ni, _make_scanner())

    @pytest.mark.parametrize(
        "title",
        ["...", "...."],
        ids=["periods-only", "many-periods"],
    )
    def test_title_empty_after_sanitize_raises(self, title: str) -> None:
        """サニタイズ後に空になるタイトル（ピリオドのみ等）は NamingInputError."""
        ni = NamingInput(
            title=title,
            document_date=date(2025, 1, 1),
            date_has_era=False,
            period=None,
            issuer=None,
        )
        with pytest.raises(NamingInputError, match="empty after sanitization"):
            build_filename(ni, _make_scanner())


# ---------------------------------------------------------------------------
# 固定文字列に '対象' を含まない (Req 4.9)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestBuildFilenameNoTaishou:
    """エンジン自身が生成する固定文字列に '対象' を含まない."""

    def test_calendar_year_no_taishou(self) -> None:
        """CALENDAR_YEAR の固定文字列に '対象' なし."""
        ni = NamingInput(
            title="テスト",
            document_date=date(2025, 1, 1),
            date_has_era=False,
            period=Period(kind=PeriodKind.CALENDAR_YEAR, year=2025),
            issuer=None,
        )
        result = build_filename(ni, _make_scanner())
        fixed_parts = result.replace("テスト", "")
        assert "対象" not in fixed_parts

    def test_fiscal_year_no_taishou(self) -> None:
        """FISCAL_YEAR の固定文字列に '対象' なし."""
        ni = NamingInput(
            title="テスト",
            document_date=date(2025, 1, 1),
            date_has_era=False,
            period=Period(
                kind=PeriodKind.FISCAL_YEAR,
                year=2025,
                start=YearMonth(year=2025, month=4),
                end=YearMonth(year=2026, month=3),
            ),
            issuer=None,
        )
        result = build_filename(ni, _make_scanner())
        fixed_parts = result.replace("テスト", "")
        assert "対象" not in fixed_parts

    def test_explicit_range_no_taishou(self) -> None:
        """EXPLICIT_RANGE の固定文字列に '対象' なし."""
        ni = NamingInput(
            title="テスト",
            document_date=date(2025, 1, 1),
            date_has_era=False,
            period=Period(
                kind=PeriodKind.EXPLICIT_RANGE,
                start=YearMonth(year=2025, month=1),
                end=YearMonth(year=2025, month=6),
            ),
            issuer=None,
        )
        result = build_filename(ni, _make_scanner())
        fixed_parts = result.replace("テスト", "")
        assert "対象" not in fixed_parts

    def test_no_period_no_taishou(self) -> None:
        """期間なしの固定文字列に '対象' なし."""
        ni = NamingInput(
            title="テスト",
            document_date=date(2025, 1, 1),
            date_has_era=False,
            period=None,
            issuer="発行元テスト",
        )
        result = build_filename(ni, _make_scanner())
        fixed_parts = result.replace("テスト", "").replace("発行元", "")
        assert "対象" not in fixed_parts


# ---------------------------------------------------------------------------
# 長さ超過時のタイトル優先短縮 (Req 5.6 integration)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestBuildFilenameLengthTruncation:
    """長さ超過時はタイトルを優先的に短縮して 200 文字以下にする."""

    def test_long_title_truncated(self) -> None:
        """タイトルが非常に長い場合、200 文字以下に短縮される."""
        long_title = "あ" * 300
        ni = NamingInput(
            title=long_title,
            document_date=date(2025, 1, 1),
            date_has_era=False,
            period=None,
            issuer=None,
        )
        result = build_filename(ni, _make_scanner())
        assert len(result) <= MAX_FILENAME_LENGTH
        assert result.endswith(".pdf")

    def test_date_preserved_on_truncation(self) -> None:
        """タイトル短縮時も日付コンポーネントは保持される."""
        long_title = "あ" * 300
        ni = NamingInput(
            title=long_title,
            document_date=date(2025, 1, 1),
            date_has_era=False,
            period=None,
            issuer=None,
        )
        result = build_filename(ni, _make_scanner())
        assert result.startswith("20250101_")

    def test_period_preserved_on_truncation(self) -> None:
        """タイトル短縮時も期間コンポーネントは保持される."""
        long_title = "い" * 300
        ni = NamingInput(
            title=long_title,
            document_date=date(2025, 1, 1),
            date_has_era=False,
            period=Period(kind=PeriodKind.CALENDAR_YEAR, year=2024),
            issuer=None,
        )
        result = build_filename(ni, _make_scanner())
        assert len(result) <= MAX_FILENAME_LENGTH
        assert "2024年分" in result

    def test_issuer_preserved_on_truncation(self) -> None:
        """タイトル短縮時も発行元コンポーネントは保持される."""
        long_title = "う" * 300
        ni = NamingInput(
            title=long_title,
            document_date=date(2025, 1, 1),
            date_has_era=False,
            period=None,
            issuer="テスト銀行",
        )
        result = build_filename(ni, _make_scanner())
        assert len(result) <= MAX_FILENAME_LENGTH
        assert "テスト銀行" in result


# ---------------------------------------------------------------------------
# 決定性 (Req 6.2)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestBuildFilenameDeterminism:
    """同一入力に対して同一出力を返す（決定的）."""

    def test_deterministic(self) -> None:
        """同じ入力で 2 回呼び出すと同じ結果."""
        scanner = _make_scanner()
        ni = NamingInput(
            title="確定申告書第一表",
            document_date=date(2026, 3, 10),
            date_has_era=True,
            period=Period(kind=PeriodKind.CALENDAR_YEAR, year=2025),
            issuer=None,
        )
        assert build_filename(ni, scanner) == build_filename(ni, scanner)
