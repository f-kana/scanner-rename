"""tests/unit/test_scanner_filename.py -- ScannerFilename パース・検証・復元のテスト.

Requirements 1.1-1.5 をカバーする。
"""

from datetime import datetime

import pytest

from scanner_rename.domain.scanner_filename import (
    parse_scanner_filename,
)


@pytest.mark.unit
class TestParseScannerFilename:
    """parse_scanner_filename の正常系テスト (Req 1.1, 1.2)."""

    def test_parse_agreed_example(self) -> None:
        """合意例 20260507132742_001.pdf をパースする."""
        result = parse_scanner_filename("20260507132742_001.pdf")
        assert result is not None
        assert result.scan_timestamp == datetime(2026, 5, 7, 13, 27, 42)
        assert result.sequence == 1

    @pytest.mark.parametrize(
        ("name", "expected_ts", "expected_seq"),
        [
            (
                "20210101000000_001.pdf",
                datetime(2021, 1, 1, 0, 0, 0),
                1,
            ),
            (
                "20231231235959_999.pdf",
                datetime(2023, 12, 31, 23, 59, 59),
                999,
            ),
            (
                "20200229120000_010.pdf",
                datetime(2020, 2, 29, 12, 0, 0),
                10,
            ),
        ],
        ids=["midnight-new-year", "end-of-year-max-seq", "leap-day"],
    )
    def test_parse_valid_filenames(
        self,
        name: str,
        expected_ts: datetime,
        expected_seq: int,
    ) -> None:
        """各種正常パターンをパースできる."""
        result = parse_scanner_filename(name)
        assert result is not None
        assert result.scan_timestamp == expected_ts
        assert result.sequence == expected_seq


@pytest.mark.unit
class TestOriginalNameRoundtrip:
    """original_name によるラウンドトリップ保証 (Req 1.5)."""

    @pytest.mark.parametrize(
        "name",
        [
            "20260507132742_001.pdf",
            "20210101000000_001.pdf",
            "20231231235959_999.pdf",
            "20200229120000_010.pdf",
        ],
        ids=["agreed-example", "midnight", "max-seq", "leap-day"],
    )
    def test_roundtrip(self, name: str) -> None:
        """パース結果の original_name が元のファイル名と一致する."""
        result = parse_scanner_filename(name)
        assert result is not None
        assert result.original_name == name

    @pytest.mark.parametrize(
        "name",
        [
            "20260507132742_001.pdf",
            "20210101000000_001.pdf",
            "20231231235959_999.pdf",
        ],
        ids=["agreed-example", "midnight", "max-seq"],
    )
    def test_parse_of_original_name_equals_result(self, name: str) -> None:
        """parse(result.original_name) == result (Postcondition)."""
        result = parse_scanner_filename(name)
        assert result is not None
        reparsed = parse_scanner_filename(result.original_name)
        assert reparsed == result


@pytest.mark.unit
class TestInvalidTimestamp:
    """カレンダー上無効な日時は None を返す (Req 1.3)."""

    @pytest.mark.parametrize(
        ("name", "reason"),
        [
            ("20261307132742_001.pdf", "month-13"),
            ("20260532132742_001.pdf", "day-32"),
            ("20260507252742_001.pdf", "hour-25"),
            ("20260507136042_001.pdf", "minute-60"),
            ("20260507132760_001.pdf", "second-60"),
            ("20260200132742_001.pdf", "feb-day-0"),
            ("20210229120000_001.pdf", "non-leap-feb-29"),
            ("20260507132742_000.pdf", "sequence-0"),
        ],
        ids=[
            "month-13",
            "day-32",
            "hour-25",
            "minute-60",
            "second-60",
            "feb-day-0",
            "non-leap-feb-29",
            "sequence-0",
        ],
    )
    def test_invalid_datetime_returns_none(self, name: str, reason: str) -> None:
        """カレンダー上存在しない日時は該当しないと判定する."""
        assert parse_scanner_filename(name) is None


@pytest.mark.unit
class TestPatternMismatch:
    """パターン不一致は None を返す (Req 1.4)."""

    @pytest.mark.parametrize(
        ("name", "reason"),
        [
            ("20260507132742_001.jpg", "wrong-extension"),
            ("20260507132742_001.PDF", "uppercase-extension"),
            ("20260507132742_001.pdf.bak", "extra-extension"),
            ("2026050713274_001.pdf", "13-digits-timestamp"),
            ("202605071327420_001.pdf", "15-digits-timestamp"),
            ("20260507132742_01.pdf", "2-digit-sequence"),
            ("20260507132742_0001.pdf", "4-digit-sequence"),
            ("20260507132742001.pdf", "no-underscore"),
            ("prefix_20260507132742_001.pdf", "prefix-before"),
            ("20260507132742_001.pdf_suffix", "suffix-after"),
            (" 20260507132742_001.pdf", "leading-space"),
            ("20260507132742_001.pdf ", "trailing-space"),
            ("", "empty-string"),
            ("not_a_scanner_file.pdf", "arbitrary-name"),
            ("20260507132742_001", "no-extension"),
            ("_needs_review_20260507132742_001.pdf", "with-prefix"),
        ],
        ids=[
            "wrong-extension",
            "uppercase-extension",
            "extra-extension",
            "13-digits",
            "15-digits",
            "2-digit-seq",
            "4-digit-seq",
            "no-underscore",
            "prefix",
            "suffix",
            "leading-space",
            "trailing-space",
            "empty",
            "arbitrary",
            "no-extension",
            "with-prefix",
        ],
    )
    def test_non_matching_returns_none(self, name: str, reason: str) -> None:
        """パターンに一致しないファイル名は該当しないと判定する."""
        assert parse_scanner_filename(name) is None


@pytest.mark.unit
class TestScannerFilenameImmutable:
    """ScannerFilename は frozen dataclass である."""

    def test_frozen(self) -> None:
        """属性の変更を禁止する."""
        result = parse_scanner_filename("20260507132742_001.pdf")
        assert result is not None
        with pytest.raises(AttributeError):
            result.sequence = 42  # type: ignore[misc]
