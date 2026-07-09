"""domain パッケージの公開 API 再エクスポート・純粋性・決定性の検証."""

from __future__ import annotations

import ast
import sys
from datetime import date, datetime
from pathlib import Path

import pytest

# ---------- 定数 ----------

_DOMAIN_PKG_DIR = (
    Path(__file__).resolve().parents[2] / "src" / "scanner_rename" / "domain"
)

# design.md Integration notes に列挙されている公開シンボル一覧
_REQUIRED_PUBLIC_SYMBOLS: set[str] = {
    # naming
    "NamingInput",
    "Period",
    "PeriodKind",
    "YearMonth",
    "build_filename",
    # scanner_filename
    "parse_scanner_filename",
    "ScannerFilename",
    # file_state
    "FileState",
    "ClassifiedFilename",
    "classify_filename",
    "with_state_prefix",
    "strip_state_prefix",
    # dedup
    "resolve_duplicate",
    # sanitize
    "sanitize_filename",
    "MAX_FILENAME_LENGTH",
    # japanese_era
    "Era",
    "EraDate",
    "to_era",
    "era_to_gregorian",
    "format_date_component",
    # errors
    "DomainError",
    "EraConversionError",
    "NamingInputError",
}

# domain 内モジュールが import して良いソース
_ALLOWED_IMPORT_PREFIXES = frozenset({"scanner_rename.domain"})


# ===================================================================
# 1. 公開 API 再エクスポート完全性 (Req 6.1)
# ===================================================================


@pytest.mark.unit
class TestPublicApiReexport:
    """domain/__init__.py が design.md の全公開シンボルを再エクスポートしていること."""

    def test_all_required_symbols_importable(self) -> None:
        """design.md に列挙された全シンボルが scanner_rename.domain から import 可能."""
        import scanner_rename.domain as domain

        missing: list[str] = []
        for sym in sorted(_REQUIRED_PUBLIC_SYMBOLS):
            if not hasattr(domain, sym):
                missing.append(sym)

        assert missing == [], f"domain パッケージに未エクスポートのシンボル: {missing}"

    def test_all_symbols_in___all__(self) -> None:
        """__all__ に全必須シンボルが含まれること."""
        import scanner_rename.domain as domain

        dunder_all = set(getattr(domain, "__all__", []))
        missing = sorted(_REQUIRED_PUBLIC_SYMBOLS - dunder_all)

        assert missing == [], f"__all__ に不足: {missing}"

    def test_reexported_objects_are_same_as_source(self) -> None:
        """再エクスポートされたオブジェクトがソースモジュールと同一であること."""
        from scanner_rename.domain import (
            ClassifiedFilename,
            DomainError,
            Era,
            EraConversionError,
            EraDate,
            FileState,
            NamingInput,
            NamingInputError,
            Period,
            PeriodKind,
            ScannerFilename,
            YearMonth,
            build_filename,
            classify_filename,
            era_to_gregorian,
            format_date_component,
            parse_scanner_filename,
            resolve_duplicate,
            sanitize_filename,
            strip_state_prefix,
            to_era,
            with_state_prefix,
        )
        from scanner_rename.domain.dedup import (
            resolve_duplicate as _resolve_duplicate,
        )
        from scanner_rename.domain.errors import (
            DomainError as _DomainError,
        )
        from scanner_rename.domain.errors import (
            EraConversionError as _EraConversionError,
        )
        from scanner_rename.domain.errors import (
            NamingInputError as _NamingInputError,
        )
        from scanner_rename.domain.file_state import (
            ClassifiedFilename as _ClassifiedFilename,
        )
        from scanner_rename.domain.file_state import (
            FileState as _FileState,
        )
        from scanner_rename.domain.file_state import (
            classify_filename as _classify_filename,
        )
        from scanner_rename.domain.file_state import (
            strip_state_prefix as _strip_state_prefix,
        )
        from scanner_rename.domain.file_state import (
            with_state_prefix as _with_state_prefix,
        )
        from scanner_rename.domain.japanese_era import Era as _Era
        from scanner_rename.domain.japanese_era import EraDate as _EraDate
        from scanner_rename.domain.japanese_era import (
            era_to_gregorian as _era_to_gregorian,
        )
        from scanner_rename.domain.japanese_era import (
            format_date_component as _format_date_component,
        )
        from scanner_rename.domain.japanese_era import to_era as _to_era
        from scanner_rename.domain.naming import (
            NamingInput as _NamingInput,
        )
        from scanner_rename.domain.naming import Period as _Period
        from scanner_rename.domain.naming import PeriodKind as _PeriodKind
        from scanner_rename.domain.naming import YearMonth as _YearMonth
        from scanner_rename.domain.naming import (
            build_filename as _build_filename,
        )
        from scanner_rename.domain.sanitize import (
            sanitize_filename as _sanitize_filename,
        )
        from scanner_rename.domain.scanner_filename import (
            ScannerFilename as _ScannerFilename,
        )
        from scanner_rename.domain.scanner_filename import (
            parse_scanner_filename as _parse_scanner_filename,
        )

        assert DomainError is _DomainError
        assert EraConversionError is _EraConversionError
        assert NamingInputError is _NamingInputError
        assert ScannerFilename is _ScannerFilename
        assert parse_scanner_filename is _parse_scanner_filename
        assert FileState is _FileState
        assert ClassifiedFilename is _ClassifiedFilename
        assert classify_filename is _classify_filename
        assert with_state_prefix is _with_state_prefix
        assert strip_state_prefix is _strip_state_prefix
        assert Era is _Era
        assert EraDate is _EraDate
        assert to_era is _to_era
        assert era_to_gregorian is _era_to_gregorian
        assert format_date_component is _format_date_component
        assert NamingInput is _NamingInput
        assert Period is _Period
        assert PeriodKind is _PeriodKind
        assert YearMonth is _YearMonth
        assert build_filename is _build_filename
        assert resolve_duplicate is _resolve_duplicate
        assert sanitize_filename is _sanitize_filename


# ===================================================================
# 2. 純粋性テスト — 標準ライブラリのみ import (Req 6.1)
# ===================================================================


def _collect_imports(source: str) -> list[str]:
    """AST を解析して import されているトップレベルモジュール名を返す."""
    tree = ast.parse(source)
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module.split(".")[0])
    return modules


@pytest.mark.unit
class TestDomainPurity:
    """domain 配下が stdlib と内部モジュール以外を import しないこと."""

    def test_no_third_party_imports(self) -> None:
        """全 .py を AST 解析し import 先が stdlib か内部のみであること."""
        stdlib_modules = sys.stdlib_module_names
        allowed_top_packages = {"scanner_rename"}

        violations: list[str] = []

        for py_file in sorted(_DOMAIN_PKG_DIR.glob("*.py")):
            source = py_file.read_text(encoding="utf-8")
            imported = _collect_imports(source)
            for mod in imported:
                if mod in stdlib_modules:
                    continue
                if mod in allowed_top_packages:
                    continue
                violations.append(f"{py_file.name}: {mod}")

        assert violations == [], (
            f"domain モジュールが非標準ライブラリを import しています: {violations}"
        )

    def test_no_io_operations_in_domain(self) -> None:
        """domain モジュールが I/O 操作を行う関数を呼び出していないこと."""
        io_functions = {
            "open",
            "print",
        }
        io_modules = {
            "os.path",
            "pathlib",
            "socket",
            "http",
            "urllib",
            "subprocess",
            "shutil",
            "tempfile",
            "io",
        }

        violations: list[str] = []

        for py_file in sorted(_DOMAIN_PKG_DIR.glob("*.py")):
            if py_file.name == "__init__.py":
                continue
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)

            # I/O モジュールの import を検出
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in io_modules:
                            violations.append(f"{py_file.name}: import {alias.name}")
                elif (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and node.module in io_modules
                ):
                    violations.append(f"{py_file.name}: from {node.module} import ...")

            # トップレベルの open/print 呼び出しを検出
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in io_functions
                ):
                    violations.append(f"{py_file.name}: {node.func.id}() call")

        assert violations == [], (
            f"domain モジュールに I/O 操作が検出されました: {violations}"
        )

    def test_domain_modules_have_no_global_mutable_state(self) -> None:
        """ミュータブルなグローバル状態がないこと.

        list/dict/set リテラルのトップレベル代入を検出する。
        正規表現コンパイル結果や frozenset 等は許可する。
        """
        mutable_containers = (ast.List, ast.Dict, ast.Set)

        violations: list[str] = []

        for py_file in sorted(_DOMAIN_PKG_DIR.glob("*.py")):
            if py_file.name == "__init__.py":
                continue
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)

            for node in ast.iter_child_nodes(tree):
                if not isinstance(node, ast.Assign):
                    continue
                # トップレベル代入のうちミュータブルリテラルを検出
                if isinstance(node.value, mutable_containers):
                    for target in node.targets:
                        name = (
                            target.id if isinstance(target, ast.Name) else "<complex>"
                        )
                        violations.append(f"{py_file.name}: mutable global '{name}'")

        assert violations == [], (
            f"domain モジュールにミュータブルなグローバル状態: {violations}"
        )


# ===================================================================
# 3. 決定性テスト — 同一入力→同一出力 (Req 6.2)
# ===================================================================


@pytest.mark.unit
class TestDeterminism:
    """同一の入力に対して常に同一の出力を返すこと."""

    _ITERATIONS = 10

    def test_parse_scanner_filename_deterministic(self) -> None:
        """parse_scanner_filename が同一入力で同一結果を返す."""
        from scanner_rename.domain import parse_scanner_filename

        name = "20260507132742_001.pdf"
        results = [parse_scanner_filename(name) for _ in range(self._ITERATIONS)]
        assert all(r == results[0] for r in results)

    def test_parse_scanner_filename_none_deterministic(self) -> None:
        """parse_scanner_filename が非一致入力で常に None を返す."""
        from scanner_rename.domain import parse_scanner_filename

        name = "not_a_scanner_file.pdf"
        results = [parse_scanner_filename(name) for _ in range(self._ITERATIONS)]
        assert all(r is None for r in results)

    def test_classify_filename_deterministic(self) -> None:
        """classify_filename が同一入力で同一結果を返す."""
        from scanner_rename.domain import classify_filename

        cases = [
            "20260507132742_001.pdf",
            "_needs_review_20260507132742_001.pdf",
            "rename_error_20260507132742_001.pdf",
            "random_document.pdf",
        ]
        for name in cases:
            results = [classify_filename(name) for _ in range(self._ITERATIONS)]
            assert all(r == results[0] for r in results), (
                f"classify_filename の非決定性: {name}"
            )

    def test_to_era_deterministic(self) -> None:
        """to_era が同一日付で同一の元号を返す."""
        from scanner_rename.domain import to_era

        d = date(2021, 10, 1)
        results = [to_era(d) for _ in range(self._ITERATIONS)]
        assert all(r == results[0] for r in results)

    def test_era_to_gregorian_deterministic(self) -> None:
        """era_to_gregorian が同一入力で同一日付を返す."""
        from scanner_rename.domain import Era, era_to_gregorian

        results = [
            era_to_gregorian(Era.REIWA, 3, 10, 1) for _ in range(self._ITERATIONS)
        ]
        assert all(r == results[0] for r in results)

    def test_format_date_component_deterministic(self) -> None:
        """format_date_component が同一入力で同一文字列を返す."""
        from scanner_rename.domain import format_date_component

        d = date(2021, 10, 1)
        results_era = [
            format_date_component(d, with_era=True) for _ in range(self._ITERATIONS)
        ]
        results_no_era = [
            format_date_component(d, with_era=False) for _ in range(self._ITERATIONS)
        ]
        assert all(r == results_era[0] for r in results_era)
        assert all(r == results_no_era[0] for r in results_no_era)

    def test_build_filename_deterministic(self) -> None:
        """build_filename が同一入力で同一ファイル名を返す."""
        from scanner_rename.domain import (
            NamingInput,
            Period,
            PeriodKind,
            ScannerFilename,
            build_filename,
        )

        scanner = ScannerFilename(
            scan_timestamp=datetime(2026, 5, 7, 13, 27, 42),
            sequence=1,
        )
        naming_input = NamingInput(
            title="確定申告書",
            document_date=date(2026, 3, 15),
            date_has_era=True,
            period=Period(
                kind=PeriodKind.CALENDAR_YEAR,
                year=2025,
            ),
            issuer="税務署",
        )
        results = [
            build_filename(naming_input, scanner) for _ in range(self._ITERATIONS)
        ]
        assert all(r == results[0] for r in results)

    def test_build_filename_minimal_deterministic(self) -> None:
        """build_filename が最小入力（期間・発行元なし）で決定的に動作する."""
        from scanner_rename.domain import (
            NamingInput,
            ScannerFilename,
            build_filename,
        )

        scanner = ScannerFilename(
            scan_timestamp=datetime(2026, 5, 7, 13, 27, 42),
            sequence=1,
        )
        naming_input = NamingInput(
            title="領収書",
            document_date=date(2026, 1, 15),
            date_has_era=False,
            period=None,
            issuer=None,
        )
        results = [
            build_filename(naming_input, scanner) for _ in range(self._ITERATIONS)
        ]
        assert all(r == results[0] for r in results)

    def test_resolve_duplicate_deterministic(self) -> None:
        """resolve_duplicate が同一入力で同一結果を返す."""
        from scanner_rename.domain import resolve_duplicate

        existing = ["test.pdf", "test_2.pdf"]
        results = [
            resolve_duplicate("test.pdf", existing) for _ in range(self._ITERATIONS)
        ]
        assert all(r == results[0] for r in results)
        assert results[0] == "test_3.pdf"

    def test_sanitize_filename_deterministic(self) -> None:
        """sanitize_filename が同一入力で同一結果を返す."""
        from scanner_rename.domain import sanitize_filename

        name = "test:file<name>with|bad*chars?.pdf"
        results = [sanitize_filename(name) for _ in range(self._ITERATIONS)]
        assert all(r == results[0] for r in results)

    def test_with_state_prefix_deterministic(self) -> None:
        """with_state_prefix が同一入力で同一結果を返す."""
        from scanner_rename.domain import (
            FileState,
            ScannerFilename,
            with_state_prefix,
        )

        scanner = ScannerFilename(
            scan_timestamp=datetime(2026, 5, 7, 13, 27, 42),
            sequence=1,
        )
        results_review = [
            with_state_prefix(scanner, FileState.NEEDS_REVIEW)
            for _ in range(self._ITERATIONS)
        ]
        results_error = [
            with_state_prefix(scanner, FileState.RENAME_ERROR)
            for _ in range(self._ITERATIONS)
        ]
        assert all(r == results_review[0] for r in results_review)
        assert all(r == results_error[0] for r in results_error)

    def test_strip_state_prefix_deterministic(self) -> None:
        """strip_state_prefix が同一入力で同一結果を返す."""
        from scanner_rename.domain import strip_state_prefix

        cases = [
            "_needs_review_20260507132742_001.pdf",
            "rename_error_20260507132742_001.pdf",
            "20260507132742_001.pdf",
        ]
        for name in cases:
            results = [strip_state_prefix(name) for _ in range(self._ITERATIONS)]
            assert all(r == results[0] for r in results), (
                f"strip_state_prefix の非決定性: {name}"
            )
