"""scanner_rename.domain -- 公開 API の再エクスポート.

消費者（extraction-pipeline）はここからのみ import する。
後のタスクで値オブジェクト・関数を追加していく。
"""

from scanner_rename.domain.errors import (
    DomainError,
    EraConversionError,
    NamingInputError,
)
from scanner_rename.domain.file_state import (
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

__all__ = [
    "ClassifiedFilename",
    "DomainError",
    "EraConversionError",
    "FileState",
    "NamingInputError",
    "ScannerFilename",
    "classify_filename",
    "parse_scanner_filename",
    "strip_state_prefix",
    "with_state_prefix",
]
