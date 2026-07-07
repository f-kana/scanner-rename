# Brief: core-naming-engine

## Problem

スキャナーが生成するファイル名（`20260507132742_001.pdf` 形式）は内容を表さず、ユーザーが Drive 上で文書を探せない。リネームパイプラインの中核となる「抽出メタデータ → 人間可読なファイル名」の変換ロジックがまだ存在しない。

## Current State

`src/scanner_rename/` は `__init__.py` のみの空パッケージ。命名フォーマットの合意事項は `docs/initial-context.md` に記録済みだが、コード化されていない。

## Desired Outcome

外部サービス依存ゼロの純 Python ドメインロジックとして、以下が unit テスト付きで動作する:

- スキャナー生成ファイル名のパースと検証（`^\d{14}_\d{3}\.pdf$`、タイムスタンプ解釈）
- 状態プレフィックス（`_needs_review_` / `rename_error_`）の付与・除去・判定（手動リトライで元名に戻せるモデル）
- 日付処理と元号変換（西暦⇔元号、`20211001(R3)` 形式の生成）
- 命名エンジン: 抽出メタデータから `<文書日付>_<年分・年度分・期間補足>_<書類タイトル>[_発行元].pdf` を生成。期間・発行元コンポーネントの省略規則を含む
- 重複サフィックス（`_2`, `_3`, ...）とファイル名サニタイズ

## Approach

ポート/アダプタ構成の最下層。I/O を一切持たない純関数・値オブジェクト群として実装し、pytest `unit` マーカーで網羅的にテストする。

## Scope

- **In**: バックログ Phase 2（PBI-ph2-001〜005）。パース、日付・元号、命名生成、重複・サニタイズ、unit テスト。
- **Out**: Drive アクセス、OCR、LLM 呼び出し、メタデータ抽出そのもの（何を抽出するかのスキーマ定義は extraction-pipeline が所有）。

## Boundary Candidates

- ファイル名の状態機械（スキャナー生成名 → 成功名 / needs_review / error）
- メタデータ → ファイル名の命名関数
- 日付・元号のユーティリティ

## Out of Boundary

- 抽出メタデータの取得方法（OCR/LLM）と信頼度判定の閾値ポリシー
- Drive 上での実リネーム操作

## Upstream / Downstream

- **Upstream**: `docs/initial-context.md` の命名合意、`app_llm_prompts/naming_policy.draft.md`
- **Downstream**: extraction-pipeline（このドメイン API の唯一の消費者）

## Existing Spec Touchpoints

- **Extends**: なし
- **Adjacent**: extraction-pipeline（抽出メタデータのデータ型がスペック間の契約になる）

## Constraints

- 外部サービス・ネットワーク I/O 禁止（デフォルトのローカルテストで完結すること）
- ファイル名に `対象` という語を使わない。年分・年度分フォーマットは initial-context.md の例に従う
