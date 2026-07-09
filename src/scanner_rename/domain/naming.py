"""命名入力の契約型・入力検証・ファイル名組み立て.

extraction-pipeline との契約面となる NamingInput / Period / YearMonth 型と、
入力検証関数 validate_naming_input、およびファイル名生成関数 build_filename を
提供する。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from scanner_rename.domain.errors import NamingInputError
from scanner_rename.domain.japanese_era import format_date_component
from scanner_rename.domain.sanitize import (
    MAX_FILENAME_LENGTH,
    sanitize_component,
    sanitize_filename,
)
from scanner_rename.domain.scanner_filename import ScannerFilename

_EXT = ".pdf"


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


def build_filename(naming_input: NamingInput, scanner: ScannerFilename) -> str:
    """命名入力とスキャナー生成名からファイル名を組み立てる.

    コンポーネント順: ``<日付>_<期間>_<タイトル>[_<発行元>].pdf``
    期間・発行元は入力に含まれない場合に省略する。
    文書日付がない場合はスキャンタイムスタンプの日付部分にフォールバックする。
    各コンポーネントをサニタイズしてから連結し、
    長さ超過時はタイトルを優先的に短縮する。

    Args:
        naming_input: 命名に必要なメタデータ
        scanner: 元ファイルのパース結果（フォールバック日付に使用）

    Returns:
        禁止文字を含まず 200 文字以下のファイル名

    Raises:
        NamingInputError: タイトル欠落・Period 必須フィールド欠落
    """
    validate_naming_input(naming_input)

    # 1. 日付コンポーネント
    doc_date = (
        naming_input.document_date
        if naming_input.document_date is not None
        else scanner.scan_timestamp.date()
    )
    date_comp = sanitize_component(
        format_date_component(doc_date, with_era=naming_input.date_has_era)
    )

    # 2. 期間コンポーネント（省略可能）
    period_comp: str | None = None
    if naming_input.period is not None:
        period_comp = sanitize_component(_format_period(naming_input.period))

    # 3. タイトルコンポーネント
    title_comp = sanitize_component(naming_input.title)
    if not title_comp:
        msg = f"title becomes empty after sanitization: {naming_input.title!r}"
        raise NamingInputError(msg)

    # 4. 発行元コンポーネント（省略可能）
    issuer_comp: str | None = None
    if naming_input.issuer is not None:
        sanitized = sanitize_component(naming_input.issuer)
        if sanitized:
            issuer_comp = sanitized

    # 5. 長さ超過時はタイトルを優先的に短縮
    title_comp = _truncate_title_if_needed(
        date_comp, period_comp, title_comp, issuer_comp
    )

    # 6. コンポーネントを連結
    parts = _assemble_components(date_comp, period_comp, title_comp, issuer_comp)
    filename = "_".join(parts) + _EXT

    # 7. 最終ガード
    return sanitize_filename(filename)


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


# --- build_filename ヘルパー ---


def _format_period(period: Period) -> str:
    """Period を文字列に整形する.

    CALENDAR_YEAR → ``YYYY年分``
    FISCAL_YEAR → ``YYYY年度分(YYYYMM-YYYYMM)``
    EXPLICIT_RANGE → ``YYYYMM-YYYYMM``
    """
    if period.kind == PeriodKind.CALENDAR_YEAR:
        return f"{period.year}年分"
    if period.kind == PeriodKind.FISCAL_YEAR:
        if period.start is None or period.end is None:
            missing = ", ".join(
                f
                for f, v in [("start", period.start), ("end", period.end)]
                if v is None
            )
            raise NamingInputError(
                f"Period(kind={period.kind.value}) requires field(s): {missing}"
            )
        start_s = _format_yearmonth(period.start)
        end_s = _format_yearmonth(period.end)
        return f"{period.year}年度分({start_s}-{end_s})"
    # EXPLICIT_RANGE
    if period.start is None or period.end is None:
        missing = ", ".join(
            f for f, v in [("start", period.start), ("end", period.end)] if v is None
        )
        raise NamingInputError(
            f"Period(kind={period.kind.value}) requires field(s): {missing}"
        )
    return f"{_format_yearmonth(period.start)}-{_format_yearmonth(period.end)}"


def _format_yearmonth(ym: YearMonth) -> str:
    """YearMonth を ``YYYYMM`` 形式に整形する."""
    return f"{ym.year:04d}{ym.month:02d}"


def _assemble_components(
    date_comp: str,
    period_comp: str | None,
    title_comp: str,
    issuer_comp: str | None,
) -> list[str]:
    """コンポーネントを順序通りに組み立てる（None は除外）."""
    parts: list[str] = [date_comp]
    if period_comp is not None:
        parts.append(period_comp)
    parts.append(title_comp)
    if issuer_comp is not None:
        parts.append(issuer_comp)
    return parts


def _truncate_title_if_needed(
    date_comp: str,
    period_comp: str | None,
    title_comp: str,
    issuer_comp: str | None,
) -> str:
    """長さ超過時にタイトルを優先的に短縮する.

    日付・期間・発行元・拡張子は保持し、タイトルのみ切り詰める。
    """
    # 現在のファイル名長を試算
    parts = _assemble_components(date_comp, period_comp, title_comp, issuer_comp)
    total = len("_".join(parts)) + len(_EXT)
    if total <= MAX_FILENAME_LENGTH:
        return title_comp

    # タイトル以外の固定長を計算
    fixed_parts = _assemble_components(date_comp, period_comp, "", issuer_comp)
    fixed_len = len("_".join(fixed_parts)) + len(_EXT)
    max_title = MAX_FILENAME_LENGTH - fixed_len

    if max_title < 1:
        max_title = 1
    return title_comp[:max_title].rstrip(" ._")


# --- validate_naming_input ヘルパー ---


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
