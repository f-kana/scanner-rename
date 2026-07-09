"""ドメイン例外階層の継承関係・型・メッセージを検証するテスト."""

import pytest

from scanner_rename.domain.errors import (
    DomainError,
    EraConversionError,
    NamingInputError,
)

# --- 継承関係 ---


@pytest.mark.unit
class TestExceptionHierarchy:
    """例外クラスの継承関係が設計どおりであることを検証する."""

    def test_domain_error_is_exception(self) -> None:
        assert issubclass(DomainError, Exception)

    def test_era_conversion_error_is_domain_error(self) -> None:
        assert issubclass(EraConversionError, DomainError)

    def test_naming_input_error_is_domain_error(self) -> None:
        assert issubclass(NamingInputError, DomainError)

    def test_era_conversion_error_is_exception(self) -> None:
        """EraConversionError は Exception としても捕捉できる."""
        assert issubclass(EraConversionError, Exception)

    def test_naming_input_error_is_exception(self) -> None:
        """NamingInputError は Exception としても捕捉できる."""
        assert issubclass(NamingInputError, Exception)

    def test_era_conversion_error_is_not_naming_input_error(self) -> None:
        """2 つの具象例外は互いに独立している."""
        assert not issubclass(EraConversionError, NamingInputError)
        assert not issubclass(NamingInputError, EraConversionError)


# --- インスタンス化とメッセージ ---


@pytest.mark.unit
class TestExceptionInstantiation:
    """例外を生成し、メッセージと raise/catch が正しく動作することを検証する."""

    def test_domain_error_message(self) -> None:
        err = DomainError("テスト用メッセージ")
        assert str(err) == "テスト用メッセージ"

    def test_era_conversion_error_message(self) -> None:
        err = EraConversionError("1867-12-31 は元号対応表の範囲外です")
        assert "1867-12-31" in str(err)
        assert "範囲外" in str(err)

    def test_naming_input_error_message(self) -> None:
        err = NamingInputError("title が空です")
        assert "title" in str(err)

    def test_raise_and_catch_domain_error(self) -> None:
        with pytest.raises(DomainError):
            raise DomainError("基底例外")

    def test_raise_era_conversion_error_caught_as_domain_error(self) -> None:
        """EraConversionError は DomainError として捕捉できる."""
        with pytest.raises(DomainError):
            raise EraConversionError("元号範囲外")

    def test_raise_naming_input_error_caught_as_domain_error(self) -> None:
        """NamingInputError は DomainError として捕捉できる."""
        with pytest.raises(DomainError):
            raise NamingInputError("入力不備")

    def test_raise_era_conversion_error_caught_specifically(self) -> None:
        with pytest.raises(EraConversionError):
            raise EraConversionError("元号範囲外")

    def test_raise_naming_input_error_caught_specifically(self) -> None:
        with pytest.raises(NamingInputError):
            raise NamingInputError("入力不備")


# --- domain パッケージからの import ---


@pytest.mark.unit
class TestDomainPackageImport:
    """scanner_rename.domain からドメイン例外を import できることを検証する."""

    def test_import_from_domain_package(self) -> None:
        from scanner_rename.domain import (
            DomainError as DE,
        )
        from scanner_rename.domain import (
            EraConversionError as ECE,
        )
        from scanner_rename.domain import (
            NamingInputError as NIE,
        )

        assert DE is DomainError
        assert ECE is EraConversionError
        assert NIE is NamingInputError
