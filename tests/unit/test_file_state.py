"""tests/unit/test_file_state.py -- 状態プレフィックス付与・除去・分類のテスト.

Requirements 2.1-2.5 をカバーする。
"""

from datetime import datetime

import pytest

from scanner_rename.domain.file_state import (
    NEEDS_REVIEW_PREFIX,
    RENAME_ERROR_PREFIX,
    ClassifiedFilename,
    FileState,
    classify_filename,
    strip_state_prefix,
    with_state_prefix,
)
from scanner_rename.domain.scanner_filename import (
    ScannerFilename,
    parse_scanner_filename,
)

# テスト用の固定値
_SAMPLE_TS = datetime(2026, 5, 7, 13, 27, 42)
_SAMPLE_SCANNER = ScannerFilename(scan_timestamp=_SAMPLE_TS, sequence=1)
_SAMPLE_NAME = "20260507132742_001.pdf"


@pytest.mark.unit
class TestPrefixConstants:
    """プレフィックス定数が設計仕様と一致する."""

    def test_needs_review_prefix(self) -> None:
        assert NEEDS_REVIEW_PREFIX == "_needs_review_"

    def test_rename_error_prefix(self) -> None:
        assert RENAME_ERROR_PREFIX == "rename_error_"

    def test_prefixes_are_distinct(self) -> None:
        """2 種のプレフィックスは相互に重複しない."""
        assert not NEEDS_REVIEW_PREFIX.startswith(RENAME_ERROR_PREFIX)
        assert not RENAME_ERROR_PREFIX.startswith(NEEDS_REVIEW_PREFIX)


@pytest.mark.unit
class TestWithStatePrefix:
    """with_state_prefix の付与テスト (Req 2.1, 2.2)."""

    def test_needs_review_prefix_applied(self) -> None:
        """Req 2.1: 低信頼度状態で _needs_review_ を先頭に付与する."""
        result = with_state_prefix(_SAMPLE_SCANNER, FileState.NEEDS_REVIEW)
        assert result == f"_needs_review_{_SAMPLE_NAME}"

    def test_rename_error_prefix_applied(self) -> None:
        """Req 2.2: エラー状態で rename_error_ を先頭に付与する."""
        result = with_state_prefix(_SAMPLE_SCANNER, FileState.RENAME_ERROR)
        assert result == f"rename_error_{_SAMPLE_NAME}"

    def test_scanner_new_raises_value_error(self) -> None:
        """SCANNER_NEW を指定すると ValueError."""
        with pytest.raises(ValueError):
            with_state_prefix(_SAMPLE_SCANNER, FileState.SCANNER_NEW)

    def test_unmanaged_raises_value_error(self) -> None:
        """UNMANAGED を指定すると ValueError."""
        with pytest.raises(ValueError):
            with_state_prefix(_SAMPLE_SCANNER, FileState.UNMANAGED)

    @pytest.mark.parametrize(
        ("name", "state", "expected"),
        [
            (
                "20210101000000_001.pdf",
                FileState.NEEDS_REVIEW,
                "_needs_review_20210101000000_001.pdf",
            ),
            (
                "20231231235959_999.pdf",
                FileState.RENAME_ERROR,
                "rename_error_20231231235959_999.pdf",
            ),
        ],
        ids=["needs-review-midnight", "error-max-seq"],
    )
    def test_various_scanner_names(
        self, name: str, state: FileState, expected: str
    ) -> None:
        """様々なスキャナー生成名に対してプレフィックスを正しく付与する."""
        scanner = parse_scanner_filename(name)
        assert scanner is not None
        assert with_state_prefix(scanner, state) == expected


@pytest.mark.unit
class TestStripStatePrefix:
    """strip_state_prefix の除去テスト (Req 2.4)."""

    def test_strip_needs_review(self) -> None:
        """_needs_review_ プレフィックスを除去する."""
        assert strip_state_prefix(f"_needs_review_{_SAMPLE_NAME}") == _SAMPLE_NAME

    def test_strip_rename_error(self) -> None:
        """rename_error_ プレフィックスを除去する."""
        assert strip_state_prefix(f"rename_error_{_SAMPLE_NAME}") == _SAMPLE_NAME

    def test_strip_no_prefix(self) -> None:
        """プレフィックスなしのファイル名はそのまま返す."""
        assert strip_state_prefix(_SAMPLE_NAME) == _SAMPLE_NAME

    def test_strip_unrelated_name(self) -> None:
        """プレフィックスなしの無関係なファイル名はそのまま返す."""
        assert strip_state_prefix("report.pdf") == "report.pdf"


@pytest.mark.unit
class TestRoundtrip:
    """strip(with_state_prefix(s, st)) == s.original_name."""

    @pytest.mark.parametrize(
        "state",
        [FileState.NEEDS_REVIEW, FileState.RENAME_ERROR],
        ids=["needs-review", "rename-error"],
    )
    def test_roundtrip_agreed_example(self, state: FileState) -> None:
        """合意例のラウンドトリップ."""
        prefixed = with_state_prefix(_SAMPLE_SCANNER, state)
        stripped = strip_state_prefix(prefixed)
        assert stripped == _SAMPLE_SCANNER.original_name

    @pytest.mark.parametrize(
        "name",
        [
            "20210101000000_001.pdf",
            "20231231235959_999.pdf",
            "20200229120000_010.pdf",
        ],
        ids=["midnight", "max-seq", "leap-day"],
    )
    @pytest.mark.parametrize(
        "state",
        [FileState.NEEDS_REVIEW, FileState.RENAME_ERROR],
        ids=["needs-review", "rename-error"],
    )
    def test_roundtrip_various(self, name: str, state: FileState) -> None:
        """各種スキャナー名 x 各プレフィックスでラウンドトリップが成立する."""
        scanner = parse_scanner_filename(name)
        assert scanner is not None
        prefixed = with_state_prefix(scanner, state)
        stripped = strip_state_prefix(prefixed)
        assert stripped == scanner.original_name


@pytest.mark.unit
class TestClassifyFilename:
    """classify_filename の 4 値分類テスト (Req 2.3, 2.5)."""

    def test_scanner_new(self) -> None:
        """未処理のスキャナー生成名を SCANNER_NEW に分類する."""
        result = classify_filename(_SAMPLE_NAME)
        assert result.state == FileState.SCANNER_NEW
        assert result.scanner_filename is not None
        assert result.scanner_filename.original_name == _SAMPLE_NAME

    def test_needs_review(self) -> None:
        """_needs_review_ プレフィックス付きを NEEDS_REVIEW に分類する."""
        result = classify_filename(f"_needs_review_{_SAMPLE_NAME}")
        assert result.state == FileState.NEEDS_REVIEW
        assert result.scanner_filename is not None
        assert result.scanner_filename.original_name == _SAMPLE_NAME

    def test_rename_error(self) -> None:
        """rename_error_ プレフィックス付きを RENAME_ERROR に分類する."""
        result = classify_filename(f"rename_error_{_SAMPLE_NAME}")
        assert result.state == FileState.RENAME_ERROR
        assert result.scanner_filename is not None
        assert result.scanner_filename.original_name == _SAMPLE_NAME

    def test_unmanaged_arbitrary_name(self) -> None:
        """無関係なファイル名を UNMANAGED に分類する."""
        result = classify_filename("report_2024.pdf")
        assert result.state == FileState.UNMANAGED
        assert result.scanner_filename is None

    def test_unmanaged_empty_string(self) -> None:
        """空文字列を UNMANAGED に分類する."""
        result = classify_filename("")
        assert result.state == FileState.UNMANAGED
        assert result.scanner_filename is None

    def test_unmanaged_prefix_only(self) -> None:
        """プレフィックスのみ（残りが空）は UNMANAGED."""
        result = classify_filename("_needs_review_")
        assert result.state == FileState.UNMANAGED
        assert result.scanner_filename is None

    def test_unmanaged_prefix_with_non_scanner_name(self) -> None:
        """Req 2.5: プレフィックス除去後が非スキャナー名なら UNMANAGED."""
        result = classify_filename("_needs_review_report.pdf")
        assert result.state == FileState.UNMANAGED
        assert result.scanner_filename is None

    def test_unmanaged_error_prefix_with_non_scanner_name(self) -> None:
        """Req 2.5: rename_error_ 後が非スキャナー名の場合も UNMANAGED."""
        result = classify_filename("rename_error_report.pdf")
        assert result.state == FileState.UNMANAGED
        assert result.scanner_filename is None

    def test_unmanaged_already_renamed(self) -> None:
        """リネーム済みファイルは UNMANAGED."""
        result = classify_filename("20211001(R3)_2025年分_確定申告書_税務署.pdf")
        assert result.state == FileState.UNMANAGED
        assert result.scanner_filename is None

    def test_no_exception_on_any_input(self) -> None:
        """classify_filename は例外を送出しない (Invariant)."""
        edge_cases = [
            "",
            " ",
            "\x00",
            "a" * 1000,
            "_needs_review_",
            "rename_error_",
            "_needs_review_rename_error_20260507132742_001.pdf",
            "rename_error__needs_review_20260507132742_001.pdf",
            ".pdf",
            "20260507132742_001.PDF",
            "/path/to/20260507132742_001.pdf",
        ]
        for name in edge_cases:
            result = classify_filename(name)
            assert isinstance(result, ClassifiedFilename)
            assert isinstance(result.state, FileState)

    def test_classify_double_needs_review_prefix(self) -> None:
        """二重プレフィックスの場合、除去後がスキャナー名でなければ UNMANAGED."""
        double = f"_needs_review__needs_review_{_SAMPLE_NAME}"
        result = classify_filename(double)
        # 最初の _needs_review_ を除去した残りは _needs_review_20260507... で
        # スキャナー名パターンに一致しないため UNMANAGED
        assert result.state == FileState.UNMANAGED
        assert result.scanner_filename is None

    def test_classify_double_error_prefix(self) -> None:
        """二重 rename_error_ は UNMANAGED."""
        double = f"rename_error_rename_error_{_SAMPLE_NAME}"
        result = classify_filename(double)
        assert result.state == FileState.UNMANAGED
        assert result.scanner_filename is None


@pytest.mark.unit
class TestClassifiedFilenameImmutable:
    """ClassifiedFilename は frozen dataclass である."""

    def test_frozen(self) -> None:
        """属性の変更を禁止する."""
        result = classify_filename(_SAMPLE_NAME)
        with pytest.raises(AttributeError):
            result.state = FileState.UNMANAGED  # type: ignore[misc]
