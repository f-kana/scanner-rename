"""命名入力の契約型と入力検証.

extraction-pipeline との契約面となる NamingInput / Period / YearMonth 型と、
入力検証関数 validate_naming_input を定義する。
build_filename は Task 6.2 で追加する。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from scanner_rename.domain.errors import NamingInputError


class PeriodKind(Enum):
    """期間の種別."""

    CALENDAR_YEAR = "calendar_year"  # YYYY年分
    FISCAL_YEAR = "fiscal_year"  # YYYY年度分(YYYYMM-YYYYMM)
    EXPLICIT_RANGE = "explicit_range"  # YYYYMM-YYYYMM


@dataclass(frozen=True)
class YearMonth:
    """年月を表す値オブジェクト."""

    year: int
    month: int  # 1..12


@dataclass(frozen=True)
class Period:
    """期間を表す値オブジェクト.

    kind に応じて必須フィールドが異なる:
    - CALENDAR_YEAR: year 必須
    - FISCAL_YEAR: year, start, end 必須
    - EXPLICIT_RANGE: start, end 必須
    """

    kind: PeriodKind
    year: int | None = None  # CALENDAR_YEAR / FISCAL_YEAR で必須
    start: YearMonth | None = None  # FISCAL_YEAR / EXPLICIT_RANGE で必須
    end: YearMonth | None = None  # FISCAL_YEAR / EXPLICIT_RANGE で必須


@dataclass(frozen=True)
class NamingInput:
    """命名エンジンへの入力契約型.

    extraction-pipeline が抽出結果からマッピングして渡す。
    """

    title: str  # 書類タイトル（必須）
    document_date: date | None  # None ならスキャンタイムスタンプにフォールバック
    date_has_era: bool  # ソース文書が元号表記か
    period: Period | None  # None なら期間コンポーネント省略
    issuer: str | None  # None なら発行元コンポーネント省略


def validate_naming_input(naming_input: NamingInput) -> None:
    """NamingInput の入力検証を行う.

    タイトルが空・空白のみ、または Period の必須フィールドが欠落している場合、
    NamingInputError を送出する。

    Raises:
        NamingInputError: 入力不備がある場合
    """
    _validate_title(naming_input.title)
    if naming_input.period is not None:
        _validate_period(naming_input.period)


def _validate_title(title: str) -> None:
    """タイトルが空・空白のみでないことを検証する."""
    if not title.strip():
        msg = "title must not be empty or whitespace-only"
        raise NamingInputError(msg)


def _validate_period(period: Period) -> None:
    """Period の必須フィールドが揃っていることを検証する."""
    missing: list[str] = []

    if period.kind == PeriodKind.CALENDAR_YEAR:
        if period.year is None:
            missing.append("year")
    elif period.kind == PeriodKind.FISCAL_YEAR:
        if period.year is None:
            missing.append("year")
        if period.start is None:
            missing.append("start")
        if period.end is None:
            missing.append("end")
    elif period.kind == PeriodKind.EXPLICIT_RANGE:
        if period.start is None:
            missing.append("start")
        if period.end is None:
            missing.append("end")

    if missing:
        fields = ", ".join(missing)
        msg = f"Period(kind={period.kind.value}) requires field(s): {fields}"
        raise NamingInputError(msg)
