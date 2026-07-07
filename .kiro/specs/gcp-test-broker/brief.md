# Brief: gcp-test-broker

## Problem

Claude Code（DevContainer 内）にクラウド統合テストを実行・自己修正させたいが、セキュリティ方針により DevContainer から Google API を直接呼ぶことも、生の GCP 認証情報を Claude Code に扱わせることもできない。この隔離を成立させる仲介者がまだ存在しない。

## Current State

`broker/` は README のみ。セキュリティ方針と隔離モデルは `docs/security-notes.md` と ADR 0004 で確定済み（ph0-020 で実態に合わせて修正済み）。

## Desired Outcome

Mac ホスト側（DevContainer の外）で動作する GCP Test Broker v0 が `broker/` に実装される:

- OCR フィクスチャと抽出フィクスチャを返すエンドポイント（決定論的なテストデータ供給）
- 目的を絞った狭い API。生の Google API プロキシにはしない
- DevContainer 内のテストコードから HTTP で呼び出せ、pytest `cloud` マーカーのテストが Broker 経由で動作する
- Broker 経由でジョブフロー全体をローカルで 1 回通す E2E 動作確認の土台になる

## Approach

ホスト側で動く小さな HTTP サービス。v0 はフィクスチャ供給に徹し、実 Google API の仲介（Document AI / Gemini / Drive の限定操作）は cloud-runtime-deploy のクラウド統合テストの要求に応じて狭い API として追加する。API 形状は本スペックが所有する。

## Scope

- **In**: バックログ Phase 4（PBI-ph4-001〜002）。Broker v0 本体、フィクスチャエンドポイント、DevContainer からの呼び出し確認。
- **Out**: アプリ本体の実アダプタ、本番デプロイ、Broker 自体のクラウドデプロイ（Broker はローカル専用）。

## Boundary Candidates

- フィクスチャ供給 API（v0 のコア）
- 実 API 仲介エンドポイント（v1 以降、消費者駆動で追加）

## Out of Boundary

- テストシナリオそのものの定義（cloud-runtime-deploy が消費者として所有）
- ポート契約の変更（extraction-pipeline が所有）

## Upstream / Downstream

- **Upstream**: extraction-pipeline（フィクスチャの形はポート契約・抽出スキーマに整合させる）、`docs/security-notes.md` の隔離モデル
- **Downstream**: cloud-runtime-deploy（クラウド統合テストが Broker を呼ぶ）

## Existing Spec Touchpoints

- **Extends**: なし
- **Adjacent**: secret-scanning（認証情報保護という同じ関心。Broker 実装が認証情報をログ・レスポンスに漏らさないこと）

## Constraints

- DevContainer は Google API を直接呼ばない。Broker のみが GCP 認証情報を使う
- Broker は狭い目的特化 API とし、汎用プロキシ化しない（`docs/security-notes.md`）
- 認証情報・トークンをレスポンスやログに含めない
- Mac ホスト上で動作（DevContainer 外）。DevContainer からはホスト向けネットワークで到達する
