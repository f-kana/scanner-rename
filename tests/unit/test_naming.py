"""tests/unit/test_naming.py -- 命名入力の契約型と入力検証のテスト.

Requirement 4.8 をカバーする。
Task 6.1: 型の不変性（frozen）と入力不備ケースの unit テスト。
"""

from __future__ import annotations

from datetime import date

import pytest

from scanner_rename.domain.errors import NamingInputError
from scanner_rename.domain.naming import (
    NamingInput,
    Period,
    PeriodKind,
    YearMonth,
    validate_naming_input,
)


# ---------------------------------------------------------------------------
# YearMonth: frozen 不変性
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestYearMonthFrozen:
    """YearMonth は frozen dataclass である."""

    def test_frozen_year(self) -> None:
        """year 属性の変更を禁止する."""
        ym = YearMonth(year=2025, month=4)
        with pytest.raises(AttributeError):
            ym.year = 2026  # type: ignore[misc]

    def test_frozen_month(self) -> None:
        """month 属性の変更を禁止する."""
        ym = YearMonth(year=2025, month=4)
        with pytest.raises(AttributeError):
            ym.month = 5  # type: ignore[misc]

    def test_equality(self) -> None:
        """同一の値を持つ YearMonth は等価である."""
        assert YearMonth(year=2025, month=4) == YearMonth(year=2025, month=4)

    def test_inequality(self) -> None:
        """異なる値を持つ YearMonth は等価でない."""
        assert YearMonth(year=2025, month=4) != YearMonth(year=2025, month=5)


# ---------------------------------------------------------------------------
# Period: frozen 不変性
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestPeriodFrozen:
    """Period は frozen dataclass である."""

    def test_frozen_kind(self) -> None:
        """kind 属性の変更を禁止する."""
        period = Period(kind=PeriodKind.CALENDAR_YEAR, year=2025)
        with pytest.raises(AttributeError):
            period.kind = PeriodKind.FISCAL_YEAR  # type: ignore[misc]

    def test_frozen_year(self) -> None:
        """year 属性の変更を禁止する."""
        period = Period(kind=PeriodKind.CALENDAR_YEAR, year=2025)
        with pytest.raises(AttributeError):
            period.year = 2026  # type: ignore[misc]

    def test_frozen_start(self) -> None:
        """start 属性の変更を禁止する."""
        period = Period(
            kind=PeriodKind.EXPLICIT_RANGE,
            start=YearMonth(year=2025, month=4),
            end=YearMonth(year=2026, month=3),
        )
        with pytest.raises(AttributeError):
            period.start = YearMonth(year=2025, month=5)  # type: ignore[misc]

    def test_defaults_are_none(self) -> None:
        """デフォルト値は None である."""
        period = Period(kind=PeriodKind.CALENDAR_YEAR)
        assert period.year is None
        assert period.start is None
        assert period.end is None


# ---------------------------------------------------------------------------
# NamingInput: frozen 不変性
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestNamingInputFrozen:
    """NamingInput は frozen dataclass である."""

    def test_frozen_title(self) -> None:
        """title 属性の変更を禁止する."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=None,
            issuer=None,
        )
        with pytest.raises(AttributeError):
            ni.title = "別のタイトル"  # type: ignore[misc]

    def test_frozen_document_date(self) -> None:
        """document_date 属性の変更を禁止する."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=None,
            issuer=None,
        )
        with pytest.raises(AttributeError):
            ni.document_date = date(2026, 1, 1)  # type: ignore[misc]

    def test_frozen_period(self) -> None:
        """period 属性の変更を禁止する."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=None,
            issuer=None,
        )
        with pytest.raises(AttributeError):
            ni.period = Period(kind=PeriodKind.CALENDAR_YEAR, year=2025)  # type: ignore[misc]

    def test_frozen_issuer(self) -> None:
        """issuer 属性の変更を禁止する."""
        ni = NamingInput(
            title="確定申告書",
            document_date=date(2025, 3, 15),
            date_has_era=False,
            period=None,
            issuer=None,
        )
        with pytest.raises(AttributeError):
            ni.issuer = "税務署"  # type: ignore[misc]

    def test_equality(self) -> None:
        """同一フィールドの NamingInput は等価である."""
        kwargs = {
            "title": "確定申告書",
            "document_date": date(2025, 3, 15),
            "date_has_era": False,
            "period": None,
            "issuer": None,
        }
        assert NamingInput(**kwargs) == NamingInput(**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# PeriodKind: Enum 値の確認
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestPeriodKindEnum:
    """PeriodKind の列挙値が設計通りである."""

    def test_calendar_year_value(self) -> None:
        assert PeriodKind.CALENDAR_YEAR.value == "calendar_year"

    def test_fiscal_year_value(self) -> None:
        assert PeriodKind.FISCAL_YEAR.value == "fiscal_year"

    def test_explicit_range_value(self) -> None:
        assert PeriodKind.EXPLICIT_RANGE.value == "explicit_range"

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
