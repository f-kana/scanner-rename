# ADR-0010: Claude Code の LSP ツール動作検証

## ステータス

候補（検証完了）

## コンテキスト

PBI-ph0-015 として、Claude Code が持つ組み込み LSP ツールの Python 対応状況を検証した。Claude Code は LSP ツールを通じて pyright をバックエンドとする言語解析機能を持っているが、実際の動作範囲は未確認だった。

### AST と LSP の関係

AST（抽象構文木）はソースコードを構造化するための技術。LSP（Language Server Protocol）は AST を内部的に利用しつつ、定義ジャンプ・参照検索・型情報取得などの高レベルな機能を標準化されたプロトコルで提供する。LSP が利用可能であれば、生の AST を直接扱う必要はほぼない。

### 検証環境

- Claude Code の組み込み LSP ツール（plugin:pyright-lsp:pyright）
- pyright 1.1.410（.venv にインストール済み）
- Python 3.13
- pyright 設定: `pyproject.toml` の `[tool.pyright]` セクション（typeCheckingMode = standard）

## 検証方法

Claude Code の LSP ツールが提供する全 9 操作を、以下の 2 種類のコードに対して実行した:

- プロジェクトコード: `src/scanner_rename/__init__.py`, `tests/test_version.py`
- 検証用サンプル: `tmp/lsp_test_sample.py`（関数呼び出し、クラス継承、ABC を含む）

## 検証結果

### 操作別の動作状況

#### 1. hover

型情報とシグネチャを取得する。

```
対象: process_documents（line 6, char 5）
結果: (function) def process_documents(docs: list[str]) -> list[str]
```

プロジェクトファイル・tmp ファイルともに動作した。

#### 2. documentSymbol

ファイル内の全シンボル（関数、クラス、メソッド、変数）をツリー構造で返す。

```
対象: tmp/lsp_test_sample.py
結果: process_documents, transform, _clean, _normalize, FileHandler（+ メソッド）,
      LocalFileHandler（+ メソッド）, RemoteFileHandler（+ メソッド）, main — 全て検出
```

プロジェクトファイル・tmp ファイルともに動作した。

#### 3. prepareCallHierarchy

指定位置の関数/メソッドの呼び出し階層アイテムを取得する。

```
対象: transform（line 10, char 5）
結果: transform (Function) - tmp/lsp_test_sample.py:10
```

プロジェクトファイル・tmp ファイルともに動作した。

#### 4. incomingCalls

指定関数の呼び出し元を特定する。

```
対象: transform（line 10, char 5）
結果: process_documents (Function) - Line 6 [calls at: 7:13]
```

プロジェクトファイル・tmp ファイルともに動作した。

#### 5. outgoingCalls

指定関数が呼び出している関数を特定する。

```
対象: transform（line 10, char 5）
結果:
  _normalize (Function) - Line 18 [called from: 11:12]
  _clean (Function) - Line 14 [called from: 11:23]
```

プロジェクトファイル・tmp ファイルともに動作した。

#### 6. goToDefinition

シンボルの定義元を特定する。

```
プロジェクトファイル:
  対象: tests/test_version.py の version（line 5, char 14）
  結果: src/scanner_rename/__init__.py:1:5 — 動作

  対象: tmp/lsp_test_sample.py の ABC（line 3, char 22）
  結果: typeshed の abc.pyi:30:5 — 動作（外部ライブラリ）

  対象: tmp/lsp_test_sample.py の process_documents 内の transform 呼び出し
  結果: No definition found — 失敗（同一ファイル内、インデックス対象外）
```

pyright のインデックス対象ファイル間では動作する。`tmp/` 内の同一ファイル参照では失敗した。

#### 7. findReferences

シンボルの全参照箇所を検索する。

```
プロジェクトファイル:
  対象: tests/test_version.py の version（line 1, char 30）
  結果: src/scanner_rename/__init__.py:1:5, tests/test_version.py:1:28, tests/test_version.py:5:12 — 動作

  対象: tmp/lsp_test_sample.py の任意のシンボル
  結果: No references found — 失敗（インデックス対象外）
```

インデックス対象ファイルでは動作する。`tmp/` ファイルでは失敗した。

#### 8. workspaceSymbol

ワークスペース全体からシンボルを名前で検索する。

```
対象: "version"
結果:
  src/scanner_rename/__init__.py: version (Function) - Line 1
  tests/test_version.py: test_version (Function) - Line 4

対象: "FileHandler"（tmp/ にのみ存在）
結果: No symbols found — 失敗（tmp/ はインデックス対象外）
```

インデックス対象ファイルでは動作する。`tmp/` のシンボルは検出されなかった。

#### 9. goToImplementation

インターフェースや抽象クラスの実装箇所を検索する。

```
対象: FileHandler（line 22, char 7）
結果: Error - "Unhandled method textDocument/implementation"
```

pyright-lsp がこの操作をサポートしていない。

### まとめ表

| 操作                 | プロジェクトファイル | tmp/ ファイル      |
| -------------------- | -------------------- | ------------------ |
| hover                | 動作                 | 動作               |
| documentSymbol       | 動作                 | 動作               |
| prepareCallHierarchy | 動作                 | 動作               |
| incomingCalls        | 動作                 | 動作               |
| outgoingCalls        | 動作                 | 動作               |
| goToDefinition       | 動作                 | 外部ライブラリのみ |
| findReferences       | 動作                 | 失敗               |
| workspaceSymbol      | 動作                 | 失敗               |
| goToImplementation   | 未サポート           | 未サポート         |

### 観察事項

- pyright のインデックス対象（`src/`, `tests/`）内のファイルでは 8/9 操作が動作する
- `tmp/` は `.gitignore` で除外されており、pyright のインデックス対象外。ファイルローカルな操作（hover, documentSymbol, call hierarchy 系）は動作するが、ワークスペース横断の操作（goToDefinition, findReferences, workspaceSymbol）は失敗する
- goToImplementation は pyright-lsp が `textDocument/implementation` メソッドを実装していないため動作しない
- Claude Code は pyright を自動検出して LSP バックエンドとして利用しており、追加の設定は不要だった
