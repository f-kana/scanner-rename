"""ドメイン層の失敗を型で区別する例外階層.

基底 DomainError と、元号範囲外 (EraConversionError)、
命名入力不備 (NamingInputError) を定義する。
例外メッセージは診断可能な内容（入力値の要約）を含む。
シークレットや長大テキストは含めない。
"""


class DomainError(Exception):
    """ドメイン層の基底例外.

    すべてのドメイン固有エラーはこのクラスを継承する。
    アプリケーション層はこの型で一括捕捉できる。
    """


class EraConversionError(DomainError):
    """元号対応表の範囲外の日付が指定された場合のエラー.

    メッセージには変換不能な入力日付を含める。
    """


class NamingInputError(DomainError):
    """命名入力の不備（タイトル欠落等）を示すエラー.

    メッセージには欠落フィールド名を含める。
    """
