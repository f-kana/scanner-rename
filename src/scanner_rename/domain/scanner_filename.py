"""スキャナー生成ファイル名のパース・検証・値オブジェクト.

パターン ``^\\d{14}_\\d{3}\\.pdf$`` の判定とタイムスタンプの
``datetime`` 変換を一箇所に集約する。不一致・無効日時は例外ではなく
``None`` で表現する（「該当しない」は正常系の分岐であるため）。
"""

import re
from dataclasses import dataclass
from datetime import datetime

_SCANNER_PATTERN = re.compile(r"^(\d{14})_(\d{3})\.pdf$")


def parse_scanner_filename(name: str) -> "ScannerFilename | None":
    """スキャナー生成ファイル名をパースし構造化された値を返す.

    パターン不一致・カレンダー上無効な日時・連番 0 は ``None`` を返す。
    戻り値が非 ``None`` のとき
    ``parse_scanner_filename(result.original_name) == result``
    が成り立つ（ラウンドトリップ保証）。
    """
    m = _SCANNER_PATTERN.match(name)
    if m is None:
        return None

    ts_str, seq_str = m.group(1), m.group(2)

    sequence = int(seq_str)
    if sequence < 1:
        return None

    scan_timestamp = _parse_timestamp(ts_str)
    if scan_timestamp is None:
        return None

    return ScannerFilename(scan_timestamp=scan_timestamp, sequence=sequence)


@dataclass(frozen=True)
class ScannerFilename:
    """スキャナー生成名の構造（タイムスタンプ + 連番）.

    不変条件: カレンダー上有効な日時、連番 1..999。
    """

    scan_timestamp: datetime
    """naive、スキャナーローカル時刻."""

    sequence: int
    """1..999 の連番（先頭ゼロ埋め 3 桁で復元）."""

    @property
    def original_name(self) -> str:
        """元のファイル名文字列を復元する.

        例: ``"20260507132742_001.pdf"``
        """
        ts = self.scan_timestamp.strftime("%Y%m%d%H%M%S")
        seq = f"{self.sequence:03d}"
        return f"{ts}_{seq}.pdf"


def _parse_timestamp(ts_str: str) -> datetime | None:
    """14 桁の文字列を YYYYMMDDhhmmss として datetime に変換する.

    カレンダー上存在しない日時は ``None`` を返す。
    """
    try:
        return datetime.strptime(ts_str, "%Y%m%d%H%M%S")
    except ValueError:
        return None
