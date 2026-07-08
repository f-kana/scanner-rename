"""scanner_rename.domain -- 公開 API の再エクスポート.

消費者（extraction-pipeline）はここからのみ import する。
後のタスクで値オブジェクト・関数を追加していく。
"""

from scanner_rename.domain.dedup import resolve_duplicate
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
from scanner_rename.domain.japanese_era import (
    Era,
    EraDate,
    era_to_gregorian,
    format_date_component,
    to_era,
)
from scanner_rename.domain.sanitize import (
    MAX_FILENAME_LENGTH,
    sanitize_component,
    sanitize_filename,
)
from scanner_rename.domain.scanner_filename import (
    ScannerFilename,
    parse_scanner_filename,
)

__all__ = [
    "ClassifiedFilename",
    "DomainError",
    "Era",
    "EraConversionError",
    "EraDate",
    "FileState",
    "MAX_FILENAME_LENGTH",
    "NamingInputError",
    "ScannerFilename",
    "classify_filename",
    "era_to_gregorian",
    "format_date_component",
    "parse_scanner_filename",
    "resolve_duplicate",
    "sanitize_component",
    "sanitize_filename",
    "strip_state_prefix",
    "to_era",
    "with_state_prefix",
]
