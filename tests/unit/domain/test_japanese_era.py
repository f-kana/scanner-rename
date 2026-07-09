"""元号テーブルと西暦⇔元号の相互変換のテスト.

各改元日の当日・前日の境界パラメタライズと双方向変換の整合を検証する。
Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""

from datetime import date

import pytest

from scanner_rename.domain.errors import EraConversionError
from scanner_rename.domain.japanese_era import (
    Era,
    era_to_gregorian,
    format_date_component,
    to_era,
)


@pytest.mark.unit
class TestEraEnum:
    """Era Enum の構造テスト."""

    def test_era_has_five_members(self) -> None:
        assert len(Era) == 5

    @pytest.mark.parametrize(
        ("era", "name_jp", "abbreviation", "start_date"),
        [
            (Era.MEIJI, "明治", "M", date(1868, 10, 23)),
            (Era.TAISHO, "大正", "T", date(1912, 7, 30)),
            (Era.SHOWA, "昭和", "S", date(1926, 12, 25)),
            (Era.HEISEI, "平成", "H", date(1989, 1, 8)),
            (Era.REIWA, "令和", "R", date(2019, 5, 1)),
        ],
    )
    def test_era_attributes(
        self, era: Era, name_jp: str, abbreviation: str, start_date: date
    ) -> None:
        """各元号が正しい名称・略号・開始日を持つ."""
        assert era.era_name == name_jp
        assert era.abbreviation == abbreviation
        assert era.start_date == start_date


@pytest.mark.unit
class TestToEra:
    """西暦→元号変換 (Req 3.2, 3.3)."""

    @pytest.mark.parametrize(
        ("gregorian", "expected_era", "expected_year"),
        [
            # 令和の開始日当日 → 令和元年 (改元日当日は新元号)
            (date(2019, 5, 1), Era.REIWA, 1),
            # 令和の開始日前日 → 平成31年
            (date(2019, 4, 30), Era.HEISEI, 31),
            # 平成の開始日当日 → 平成元年
            (date(1989, 1, 8), Era.HEISEI, 1),
            # 平成の開始日前日 → 昭和64年
            (date(1989, 1, 7), Era.SHOWA, 64),
            # 昭和の開始日当日 → 昭和元年
            (date(1926, 12, 25), Era.SHOWA, 1),
            # 昭和の開始日前日 → 大正15年
            (date(1926, 12, 24), Era.TAISHO, 15),
            # 大正の開始日当日 → 大正元年
            (date(1912, 7, 30), Era.TAISHO, 1),
            # 大正の開始日前日 → 明治45年
            (date(1912, 7, 29), Era.MEIJI, 45),
            # 明治の開始日当日 → 明治元年
            (date(1868, 10, 23), Era.MEIJI, 1),
            # 令和の一般的な日付
            (date(2021, 10, 1), Era.REIWA, 3),
            # 令和7年の一般的な日付
            (date(2025, 6, 15), Era.REIWA, 7),
            # 昭和の一般的な日付
            (date(1980, 3, 15), Era.SHOWA, 55),
        ],
    )
    def test_to_era(
        self, gregorian: date, expected_era: Era, expected_year: int
    ) -> None:
        result = to_era(gregorian)
        assert result.era == expected_era
        assert result.year == expected_year

    def test_to_era_before_meiji_raises(self) -> None:
        """明治の開始日より前の日付は EraConversionError (Req 3.6)."""
        with pytest.raises(EraConversionError):
            to_era(date(1868, 10, 22))

    def test_to_era_very_old_date_raises(self) -> None:
        """非常に古い日付も EraConversionError."""
        with pytest.raises(EraConversionError):
            to_era(date(1600, 1, 1))


@pytest.mark.unit
class TestEraToGregorian:
    """元号→西暦変換 (Req 3.1, 3.3)."""

    @pytest.mark.parametrize(
        ("era", "year", "month", "day", "expected"),
        [
            # 令和元年5月1日（改元日当日）
            (Era.REIWA, 1, 5, 1, date(2019, 5, 1)),
            # 令和3年10月1日
            (Era.REIWA, 3, 10, 1, date(2021, 10, 1)),
            # 平成元年1月8日（改元日当日）
            (Era.HEISEI, 1, 1, 8, date(1989, 1, 8)),
            # 平成31年4月30日（平成最終日）
            (Era.HEISEI, 31, 4, 30, date(2019, 4, 30)),
            # 昭和元年12月25日（改元日当日）
            (Era.SHOWA, 1, 12, 25, date(1926, 12, 25)),
            # 昭和64年1月7日（昭和最終日）
            (Era.SHOWA, 64, 1, 7, date(1989, 1, 7)),
            # 大正元年7月30日（改元日当日）
            (Era.TAISHO, 1, 7, 30, date(1912, 7, 30)),
            # 大正15年12月24日（大正最終日）
            (Era.TAISHO, 15, 12, 24, date(1926, 12, 24)),
            # 明治元年10月23日（明治開始日）
            (Era.MEIJI, 1, 10, 23, date(1868, 10, 23)),
            # 明治45年7月29日（明治最終日）
            (Era.MEIJI, 45, 7, 29, date(1912, 7, 29)),
        ],
    )
    def test_era_to_gregorian(
        self, era: Era, year: int, month: int, day: int, expected: date
    ) -> None:
        assert era_to_gregorian(era, year, month, day) == expected

    def test_era_to_gregorian_year_zero_raises(self) -> None:
        """元号年 0 は無効 (Req 3.6)."""
        with pytest.raises(EraConversionError):
            era_to_gregorian(Era.REIWA, 0, 5, 1)

    def test_era_to_gregorian_negative_year_raises(self) -> None:
        """負の元号年は無効."""
        with pytest.raises(EraConversionError):
            era_to_gregorian(Era.REIWA, -1, 5, 1)

    def test_era_to_gregorian_date_before_era_start_raises(self) -> None:
        """元号の開始日より前の日付は EraConversionError.

        令和元年4月30日は平成であり令和ではないため変換不能。
        """
        with pytest.raises(EraConversionError):
            era_to_gregorian(Era.REIWA, 1, 4, 30)

    def test_era_to_gregorian_date_after_era_end_raises(self) -> None:
        """元号の終了日より後の日付は EraConversionError.

        平成31年5月1日は令和であり平成ではないため変換不能。
        """
        with pytest.raises(EraConversionError):
            era_to_gregorian(Era.HEISEI, 31, 5, 1)

    def test_era_to_gregorian_meiji_before_start_raises(self) -> None:
        """明治元年10月22日は明治の開始日前なので変換不能."""
        with pytest.raises(EraConversionError):
            era_to_gregorian(Era.MEIJI, 1, 10, 22)

    def test_era_to_gregorian_invalid_calendar_date_raises(self) -> None:
        """カレンダー上存在しない日付は EraConversionError."""
        with pytest.raises(EraConversionError):
            era_to_gregorian(Era.REIWA, 3, 2, 30)


@pytest.mark.unit
class TestBidirectionalConsistency:
    """双方向変換の整合テスト (Req 3.1, 3.2)."""

    @pytest.mark.parametrize(
        ("era", "year", "month", "day"),
        [
            (Era.REIWA, 1, 5, 1),
            (Era.REIWA, 3, 10, 1),
            (Era.HEISEI, 1, 1, 8),
            (Era.HEISEI, 31, 4, 30),
            (Era.SHOWA, 1, 12, 25),
            (Era.SHOWA, 64, 1, 7),
            (Era.TAISHO, 1, 7, 30),
            (Era.TAISHO, 15, 12, 24),
            (Era.MEIJI, 1, 10, 23),
            (Era.MEIJI, 45, 7, 29),
        ],
    )
    def test_gregorian_roundtrip(
        self, era: Era, year: int, month: int, day: int
    ) -> None:
        """era_to_gregorian → to_era のラウンドトリップが一致する."""
        gregorian = era_to_gregorian(era, year, month, day)
        result = to_era(gregorian)
        assert result.era == era
        assert result.year == year

    @pytest.mark.parametrize(
        "gregorian",
        [
            date(2019, 5, 1),
            date(2019, 4, 30),
            date(1989, 1, 8),
            date(1989, 1, 7),
            date(1926, 12, 25),
            date(1926, 12, 24),
            date(1912, 7, 30),
            date(1912, 7, 29),
            date(1868, 10, 23),
            date(2021, 10, 1),
        ],
    )
    def test_era_roundtrip(self, gregorian: date) -> None:
        """to_era → era_to_gregorian のラウンドトリップが元の日付と一致する."""
        era_date = to_era(gregorian)
        restored = era_to_gregorian(
            era_date.era, era_date.year, gregorian.month, gregorian.day
        )
        assert restored == gregorian


@pytest.mark.unit
class TestFormatDateComponent:
    """ファイル名用の日付コンポーネント整形テスト (Req 3.4, 3.5)."""

    def test_with_era_reiwa_3(self) -> None:
        """令和3年10月1日を元号付きで整形 → 20211001(R3) (Req 3.4)."""
        result = format_date_component(date(2021, 10, 1), with_era=True)
        assert result == "20211001(R3)"

    def test_without_era(self) -> None:
        """西暦のみ整形 → YYYYMMDD (Req 3.5)."""
        result = format_date_component(date(2021, 10, 1), with_era=False)
        assert result == "20211001"

    def test_with_era_year_one(self) -> None:
        """元号年 1 は R1 のように数字 1 を用いる（元年ではない）."""
        result = format_date_component(date(2019, 5, 1), with_era=True)
        assert result == "20190501(R1)"

    @pytest.mark.parametrize(
        ("d", "expected"),
        [
            # 平成元年
            (date(1989, 1, 8), "19890108(H1)"),
            # 平成31年（平成最終日）
            (date(2019, 4, 30), "20190430(H31)"),
            # 昭和元年
            (date(1926, 12, 25), "19261225(S1)"),
            # 昭和64年（昭和最終日）
            (date(1989, 1, 7), "19890107(S64)"),
            # 大正元年
            (date(1912, 7, 30), "19120730(T1)"),
            # 明治元年
            (date(1868, 10, 23), "18681023(M1)"),
        ],
    )
    def test_with_era_various_eras(self, d: date, expected: str) -> None:
        """各元号での整形が正しい."""
        assert format_date_component(d, with_era=True) == expected

    def test_without_era_zero_padded(self) -> None:
        """月日が 1 桁の場合もゼロ埋めされる."""
        result = format_date_component(date(2025, 1, 5), with_era=False)
        assert result == "20250105"

    def test_with_era_zero_padded(self) -> None:
        """元号付きでも月日がゼロ埋めされる."""
        result = format_date_component(date(2025, 1, 5), with_era=True)
        assert result == "20250105(R7)"
