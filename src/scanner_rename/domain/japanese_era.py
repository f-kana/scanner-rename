"""西暦⇔元号の相互変換.

明治・大正・昭和・平成・令和の改元日を持つ静的テーブルを定義し、
西暦→元号+元号年、元号+年月日→西暦の双方向変換を提供する。
改元日当日は新元号として扱う。

Requirements: 3.1, 3.2, 3.3, 3.6
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from scanner_rename.domain.errors import EraConversionError


class Era(Enum):
    """日本の元号.

    value は (名称, 略号, 開始日) のタプル。
    改元日当日は新元号に属する。
    将来の改元はメンバーを 1 行追加するだけで対応できる。
    """

    MEIJI = ("明治", "M", date(1868, 10, 23))
    TAISHO = ("大正", "T", date(1912, 7, 30))
    SHOWA = ("昭和", "S", date(1926, 12, 25))
    HEISEI = ("平成", "H", date(1989, 1, 8))
    REIWA = ("令和", "R", date(2019, 5, 1))

    @property
    def era_name(self) -> str:
        """元号の日本語名称（例: '令和'）."""
        return self.value[0]

    @property
    def abbreviation(self) -> str:
        """元号の略号（例: 'R'）."""
        return self.value[1]

    @property
    def start_date(self) -> date:
        """元号の開始日（改元日）."""
        return self.value[2]


@dataclass(frozen=True)
class EraDate:
    """元号と元号年を保持する値オブジェクト.

    元号年 1 は元年を表す。
    """

    era: Era
    year: int  # 元号年（1 = 元年）


def to_era(d: date) -> EraDate:
    """西暦の日付を元号と元号年に変換する.

    改元日当日は新元号として判定する。
    明治の開始日 (1868-10-23) より前の日付は変換不能として
    EraConversionError を送出する。

    Args:
        d: 変換対象の西暦日付

    Returns:
        対応する EraDate

    Raises:
        EraConversionError: 対応表の範囲外（明治開始日より前）
    """
    era = _find_era_for_date(d)
    year = d.year - era.start_date.year + 1
    return EraDate(era=era, year=year)


def era_to_gregorian(era: Era, year: int, month: int, day: int) -> date:
    """元号・元号年・月・日を西暦の日付に変換する.

    変換結果がその元号の適用期間内であることを検証する。
    範囲外指定は EraConversionError を送出する。

    Args:
        era: 元号
        year: 元号年（1 以上）
        month: 月（1-12）
        day: 日

    Returns:
        対応する西暦の date

    Raises:
        EraConversionError: 元号年が 0 以下、カレンダー上無効、
                            または指定日がその元号の適用期間外
    """
    if year < 1:
        msg = f"元号年は 1 以上である必要があります: {era.era_name}{year}年"
        raise EraConversionError(msg)

    gregorian_year = era.start_date.year + year - 1

    try:
        result = date(gregorian_year, month, day)
    except ValueError as e:
        msg = (
            f"カレンダー上無効な日付です: "
            f"{era.era_name}{year}年{month}月{day}日 "
            f"(西暦 {gregorian_year}年{month}月{day}日)"
        )
        raise EraConversionError(msg) from e

    _validate_date_in_era(result, era)
    return result


# --- ヘルパー関数 ---


def _find_era_for_date(d: date) -> Era:
    """日付に対応する元号を検索する（開始日が新しい順に走査）."""
    for era in reversed(Era):
        if d >= era.start_date:
            return era
    msg = f"対応表の範囲外の日付です（明治以前）: {d.isoformat()}"
    raise EraConversionError(msg)


def _validate_date_in_era(d: date, era: Era) -> None:
    """日付がその元号の適用期間内であることを検証する."""
    if d < era.start_date:
        msg = (
            f"指定日 {d.isoformat()} は"
            f"{era.era_name}の開始日 {era.start_date.isoformat()} より前です"
        )
        raise EraConversionError(msg)

    next_era = _get_next_era(era)
    if next_era is not None and d >= next_era.start_date:
        msg = (
            f"指定日 {d.isoformat()} は"
            f"{era.era_name}の終了後（{next_era.era_name}の期間内）です"
        )
        raise EraConversionError(msg)


def _get_next_era(era: Era) -> Era | None:
    """指定した元号の次の元号を返す。最後の元号なら None."""
    members = list(Era)
    idx = members.index(era)
    if idx + 1 < len(members):
        return members[idx + 1]
    return None
