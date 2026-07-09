"""Drive ファイル名で表現される処理状態の分類と相互変換.

プレフィックス文字列定数 ``NEEDS_REVIEW_PREFIX`` / ``RENAME_ERROR_PREFIX``
はこのモジュールのみが所有する。分類は「未処理スキャナー生成名 / needs_review
/ rename_error / 処理対象外」の 4 値。
"""

from dataclasses import dataclass
from enum import Enum

from scanner_rename.domain.scanner_filename import (
    ScannerFilename,
    parse_scanner_filename,
)

NEEDS_REVIEW_PREFIX: str = "_needs_review_"
RENAME_ERROR_PREFIX: str = "rename_error_"


class FileState(Enum):
    """ファイル名から判別される処理状態."""

    SCANNER_NEW = "scanner_new"
    NEEDS_REVIEW = "needs_review"
    RENAME_ERROR = "rename_error"
    UNMANAGED = "unmanaged"


@dataclass(frozen=True)
class ClassifiedFilename:
    """ファイル名の状態分類結果.

    ``UNMANAGED`` のとき ``scanner_filename`` は ``None``、
    それ以外では必ず非 ``None``。
    """

    state: FileState
    scanner_filename: ScannerFilename | None


def classify_filename(name: str) -> ClassifiedFilename:
    """任意のファイル名を 4 値に分類する.

    例外を送出しない（全入力を 4 値のいずれかに分類する）。
    """
    # needs_review プレフィックスのチェック
    if name.startswith(NEEDS_REVIEW_PREFIX):
        remainder = name[len(NEEDS_REVIEW_PREFIX) :]
        scanner = parse_scanner_filename(remainder)
        if scanner is not None:
            return ClassifiedFilename(
                state=FileState.NEEDS_REVIEW, scanner_filename=scanner
            )
        return ClassifiedFilename(state=FileState.UNMANAGED, scanner_filename=None)

    # rename_error プレフィックスのチェック
    if name.startswith(RENAME_ERROR_PREFIX):
        remainder = name[len(RENAME_ERROR_PREFIX) :]
        scanner = parse_scanner_filename(remainder)
        if scanner is not None:
            return ClassifiedFilename(
                state=FileState.RENAME_ERROR, scanner_filename=scanner
            )
        return ClassifiedFilename(state=FileState.UNMANAGED, scanner_filename=None)

    # プレフィックスなし: スキャナー生成名かどうか
    scanner = parse_scanner_filename(name)
    if scanner is not None:
        return ClassifiedFilename(state=FileState.SCANNER_NEW, scanner_filename=scanner)

    return ClassifiedFilename(state=FileState.UNMANAGED, scanner_filename=None)


def with_state_prefix(scanner: ScannerFilename, state: FileState) -> str:
    """スキャナー生成名に状態プレフィックスを付与する.

    ``state`` は ``NEEDS_REVIEW`` または ``RENAME_ERROR`` のみ許可する。
    それ以外は ``ValueError`` を送出する。
    """
    if state is FileState.NEEDS_REVIEW:
        return f"{NEEDS_REVIEW_PREFIX}{scanner.original_name}"
    if state is FileState.RENAME_ERROR:
        return f"{RENAME_ERROR_PREFIX}{scanner.original_name}"
    msg = (
        f"with_state_prefix に指定できる state は "
        f"NEEDS_REVIEW または RENAME_ERROR のみです: {state!r}"
    )
    raise ValueError(msg)


def strip_state_prefix(name: str) -> str:
    """ファイル名から状態プレフィックスを除去する.

    プレフィックスがなければそのまま返す。
    """
    if name.startswith(NEEDS_REVIEW_PREFIX):
        return name[len(NEEDS_REVIEW_PREFIX) :]
    if name.startswith(RENAME_ERROR_PREFIX):
        return name[len(RENAME_ERROR_PREFIX) :]
    return name
