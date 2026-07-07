# Roadmap

## Overview

Brother スキャナーが Google Drive `/From_BrotherDevice` にアップロードする PDF を、Document AI OCR + Gemini 構造化出力で解析し、内容に基づいて自動リネームするシステム（v1）。Cloud Scheduler → Cloud Run Job のポーリング型バッチとして動作し、状態は Drive ファイル名のプレフィックスで表現する（外部ステートストアなし）。

PBI-ph1-001 の Discovery（2026-07-08）で、プロダクトバックログ Phase 2〜6 を 4 スペックに分解した。バックログが指摘していた不足観点（LLM プロンプト設計、Gemini 構造化出力スキーマ、エラーハンドリング・リトライ戦略、Broker 経由のローカル E2E）は各スペックのスコープに割り当て済み。

## Approach Decision

- **Chosen**: 4 スペック分割。純ドメイン / アプリケーションパイプライン / ホスト側テストブローカー / クラウド実体・デプロイ、というランタイムと責務の境界で切る。
- **Why**: 各スペックが 5〜14 タスク程度に収まり、レビュー範囲が明確。GCP Test Broker は別ランタイム（Mac ホスト側）かつセキュリティ境界そのものであり、独立した設計・レビューに値する。
- **Rejected alternatives**:
  - 単一スペック: Phase 2〜6 + 不足観点で 25〜40 タスク規模となり、cc-sdd の 20 タスク上限ガイドラインに反する。
  - 3 スペック分割（Phase 4+5+6 を 1 つに集約）: 開発インフラ（Broker）・本番コード（実アダプタ）・運用（デプロイ/監視）が 1 スペックに混在し、責務の継ぎ目が濁る。
  - 5 スペック分割（実アダプタとデプロイ/監視も分離）: 小規模個人プロジェクトにはセレモニー過多。

## Scope

- **In**: v1 のポーリング型リネームパイプライン全体。フィクスチャベースのローカルテスト基盤（フェイクアダプタ + GCP Test Broker）、Cloud Run Job デプロイ、ログベースアラートによるメール通知まで。
- **Out**: Drive プッシュ通知、Firestore 等の外部ステートストア、複数文書 PDF の分割、元ファイルのバックアップ、Gmail API による直接通知、Slack 通知。

## Constraints

- Python + uv、Cloud Run Job（ADR 0001）。ポーリングファースト（ADR 0002）。ステートストアなし・Drive ファイル名で状態表現（ADR 0003）。
- クラウド統合テストは DevContainer から直接 Google API を呼ばず、ホスト側 GCP Test Broker 経由のみ（ADR 0004、`docs/security-notes.md`）。Broker は目的を絞った狭い API とし、生プロキシにしない。
- 命名ポリシー等のランタイム LLM プロンプトは YAML ルールセットではなく `app_llm_prompts/` の自然言語 Markdown で管理（ADR 0005）。
- テストは pytest マーカー `unit` / `integration_fake` / `cloud` / `e2e_cloud` で分類し、デフォルトのローカルテストは外部サービス不要。

## Boundary Strategy

- **Why this split**: I/O ゼロの純ドメイン（core-naming-engine）を最下層に置き、ポート/アダプタでアプリフロー（extraction-pipeline）を組み、テスト基盤（gcp-test-broker）とクラウド実体（cloud-runtime-deploy）を分離することで、各スペックが独立に実装・検証可能になる。Broker とパイプラインはポート定義（インターフェース）だけで疎結合。
- **Shared seams to watch**:
  - extraction-pipeline が定義するポート（Drive / OCR / LLM 抽出インターフェース）は、フェイクアダプタ・Broker フィクスチャ・実アダプタの 3 者が共有する契約。変更時は 3 スペック横断レビューが必要。
  - エラーハンドリングは 2 層に分かれる: アプリレベルの状態遷移（`_needs_review_` / `rename_error_`）は extraction-pipeline、インフラレベルのリトライ（Cloud Run Job 再試行、Drive API レート制限）は cloud-runtime-deploy が持つ。
  - Broker の API 形状は gcp-test-broker が所有するが、クラウド統合テスト（cloud-runtime-deploy）が消費者。拡張が必要な場合は gcp-test-broker 側を更新する。

## Specs (dependency order)

- [x] core-naming-engine -- 純 Python ドメインロジック（ファイル名パース/検証、日付・元号変換、命名エンジン、重複サフィックス・サニタイズ）。Dependencies: none
- [x] extraction-pipeline -- ポート定義、フェイクアダプタ、Gemini 構造化出力スキーマ、プロンプト素材、アプリフロー全体、integration_fake テスト。Dependencies: core-naming-engine
- [x] gcp-test-broker -- Mac ホスト側 GCP Test Broker v0（OCR/抽出フィクスチャ用の狭い API、`broker/` に実装 + ルート `tests/cloud/` の conftest・到達確認）。Dependencies: extraction-pipeline
- [x] cloud-runtime-deploy -- 実アダプタ（Drive API / Document AI / Gemini）、Broker 経由クラウド統合テスト、Cloud Run Job パッケージング、構造化ログ・監視アラート、Cloud Scheduler。Dependencies: extraction-pipeline, gcp-test-broker

（チェックは「スペック作成完了」を示す。実装状況は各スペックの tasks.md と `/kiro-spec-status` を正とする）
