# Brief: extraction-pipeline

## Problem

PDF を検出してから Drive 上でリネームするまでのアプリケーションフロー全体（検索 → OCR → LLM 抽出 → 命名 → リネーム → 状態遷移）がまだ存在しない。また、外部サービス（Drive / Document AI / Gemini）に依存せずにこのフローを検証する手段がない。

## Current State

core-naming-engine（純ドメイン）が別スペックで定義済み。ポート定義・アプリケーションサービス・フェイクアダプタは未着手。Gemini への抽出指示素材は `app_llm_prompts/*.draft.md` にドラフトのみ存在する。

## Desired Outcome

- Drive / OCR / LLM 抽出の 3 ポート（インターフェース）が定義され、フェイクアダプタで差し替え可能
- アプリケーションフロー全体（`/From_BrotherDevice` 直下のパターン一致 PDF を列挙 → OCR → 構造化抽出 → 命名 → リネーム、失敗時は `_needs_review_` / `rename_error_` 遷移）が実装される
- Gemini 構造化出力のスキーマ（文書日付、元号、タイトル、発行者、文書種別、年分・年度分・明示期間、信頼度、エビデンス抜粋）が入出力型として定義される
- 抽出・命名ポリシーのランタイムプロンプト素材が `app_llm_prompts/` で確定版になる
- アプリレベルのエラーハンドリングポリシー（低信頼度と技術エラーの分岐、1 ファイルの失敗が他ファイルの処理を止めない）が定義される
- pytest `integration_fake` でフロー全体が外部サービスなしで検証できる

## Approach

ポート/アダプタ（ヘキサゴナル）。ポートは extraction-pipeline が所有し、フェイク・Broker フィクスチャ・実アダプタの 3 実装が同じ契約に従う。プロンプトは ADR 0005 に従い自然言語 Markdown で管理する。

## Scope

- **In**: バックログ Phase 3（PBI-ph3-001〜003）+ 不足観点のうち「LLM プロンプト設計」「Gemini 構造化出力スキーマ」「アプリレベルのエラーハンドリング」。
- **Out**: 実アダプタ実装、Broker、インフラレベルのリトライ（Cloud Run 再試行、API レート制限）、デプロイ。

## Boundary Candidates

- ポート定義（契約）とアプリケーションサービス（オーケストレーション）
- フェイクアダプタ群
- 抽出スキーマ + プロンプト素材

## Out of Boundary

- 命名規則そのもの（core-naming-engine が所有）
- Google API の呼び出し方法・認証（cloud-runtime-deploy が所有）

## Upstream / Downstream

- **Upstream**: core-naming-engine（ドメイン API とメタデータ型）
- **Downstream**: gcp-test-broker（フィクスチャ API はポート契約に整合させる）、cloud-runtime-deploy（実アダプタが同じポートを実装）

## Existing Spec Touchpoints

- **Extends**: なし
- **Adjacent**: core-naming-engine、gcp-test-broker、cloud-runtime-deploy（ポート契約が 3 スペック共有のシーム）

## Constraints

- デフォルトのローカルテストは外部サービス不要（`unit` / `integration_fake` のみで検証可能なこと）
- 1 PDF = 1 文書。複数文書 PDF の分割はしない
- 命名ポリシーは YAML ルールセット化せず、`app_llm_prompts/` の自然言語プロンプトで表現する（ADR 0005）
