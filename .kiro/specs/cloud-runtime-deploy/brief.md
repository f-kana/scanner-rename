# Brief: cloud-runtime-deploy

## Problem

パイプラインがフェイクアダプタ上で動いても、実際の Google Drive / Document AI / Gemini に接続され、Cloud Run Job として定期実行され、失敗がメールで通知されなければプロダクトとして価値を生まない。

## Current State

extraction-pipeline がポート契約とフェイク実装を、gcp-test-broker がテスト用の仲介 API を提供済み（依存スペック）。実アダプタ・デプロイ構成・監視は未着手。

## Desired Outcome

- Drive API / Document AI / Gemini の実アダプタが、extraction-pipeline のポート契約を実装する
- インフラレベルのエラーハンドリング・リトライ戦略（Cloud Run Job の再試行との整合、Drive API レート制限、LLM 呼び出し失敗時の扱い）が設計・実装される
- pytest `cloud` / `e2e_cloud` テストが Broker 経由で動作し、Broker 経由でジョブ全体を 1 回通すローカル E2E が確認できる
- Cloud Run Job としてパッケージングされる（Dockerfile、エントリポイント）
- 構造化ログ → Cloud Logging → Cloud Monitoring ログベースアラート → fumiaki.k@gmail.com へのメール通知（`needs_review` と `error` のみ、成功時は通知しない）
- Cloud Scheduler による 5 分ごとの定期実行

## Approach

実アダプタは Broker 経由のクラウド統合テストで検証してからデプロイする。デプロイは Cloud Run Job + Cloud Scheduler の最小構成（ADR 0001, 0002）。通知は Gmail API を使わず、ログベースアラートで実現する。

## Scope

- **In**: バックログ Phase 5 + 6（PBI-ph5-001〜002、PBI-ph6-001〜003）+ 不足観点のうち「インフラレベルのリトライ戦略」「ローカル E2E（Broker 経由でジョブ全体を 1 回通す）」。
- **Out**: Drive プッシュ通知、Firestore、Gmail API 直接送信、Terraform/IaC の本格整備（デプロイ手順は最小限のスクリプト/手順書とし、IaC 化は将来 PBI）。

## Boundary Candidates

- 実アダプタ 3 種（Drive / Document AI / Gemini）
- パッケージング + デプロイ（Dockerfile、Cloud Run Job、Scheduler）
- 可観測性（構造化ログ、ログベースアラート）

## Out of Boundary

- ポート契約の定義・変更（extraction-pipeline が所有）
- Broker API の形状（gcp-test-broker が所有。テスト要件から拡張が必要な場合は gcp-test-broker 側を更新する）

## Upstream / Downstream

- **Upstream**: extraction-pipeline（ポート契約）、gcp-test-broker（クラウド統合テストの経路）
- **Downstream**: なし（v1 の最終スペック）

## Existing Spec Touchpoints

- **Extends**: なし
- **Adjacent**: gcp-test-broker（テスト経路）、secret-scanning（デプロイ関連ファイルに認証情報を含めない）

## Constraints

- クラウド統合テストは DevContainer から直接 Google API を呼ばず、必ず Broker 経由（`docs/security-notes.md`）
- 本番ランタイム（Cloud Run Job）はサービスアカウントで直接 Google API を呼ぶ（Broker はローカル開発専用）
- 状態は Drive ファイル名のみで表現（ADR 0003）。冪等性: 同一ファイルの再処理が二重リネームや誤課金を生まないこと
- 通知は Cloud Monitoring ログベースアラートのみ。v1 で Gmail API 直接送信は実装しない
