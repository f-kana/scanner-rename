# Requirements Document

## Project Description (Input)

パイプラインがフェイクアダプタ上で動いても、実際の Google Drive / Document AI / Gemini に接続され、Cloud Run Job として定期実行され、失敗がメールで通知されなければプロダクトとして価値を生まない。extraction-pipeline がポート契約とフェイク実装を、gcp-test-broker がテスト用の仲介 API を提供済みだが、実アダプタ・デプロイ構成・監視は未着手である。

本機能 cloud-runtime-deploy は以下を実現する: Drive API / Document AI / Gemini の実アダプタが extraction-pipeline のポート契約を実装する。インフラレベルのエラーハンドリング・リトライ戦略（Cloud Run Job の再試行との整合、Drive API レート制限、LLM 呼び出し失敗時の扱い、ファイル名による状態表現の下での冪等性）を設計・実装する。pytest `cloud` / `e2e_cloud` テストが Broker 経由で動作し、Broker 経由でジョブ全体を 1 回通すローカル E2E が確認できる。Cloud Run Job としてパッケージングされる（Dockerfile、エントリポイント）。構造化ログ → Cloud Logging → Cloud Monitoring ログベースアラート → fumiaki.k@gmail.com へのメール通知（`needs_review` と `error` のみ、成功時は通知しない）。Cloud Scheduler による 5 分ごとの定期実行。デプロイは最小限のスクリプト・手順書とし、IaC 化は将来 PBI とする。

## Introduction

本機能は、スキャン PDF 自動リネームシステムの v1 を本番稼働させる最終スペックである。extraction-pipeline が定義したポート契約（Drive / OCR / LLM 抽出）に対する実アダプタを実装し、パイプラインを Cloud Run Job としてパッケージングして Cloud Scheduler で 5 分ごとに起動し、要確認・エラーの発生を構造化ログ経由のメール通知で運用者に届ける。クラウド統合テストは DevContainer から Google API を直接呼ばず、必ずホスト側 GCP Test Broker 経由で実行する（`docs/security-notes.md`）。本番の Cloud Run Job のみがサービスアカウントで Google API を直接呼ぶ（Broker はローカル開発専用）。

## Boundary Context

- In scope: 実アダプタ 3 種（Google Drive API / Document AI / Gemini）、インフラレベルのリトライ戦略と冪等性の担保、ジョブのエントリポイントと実行時設定、コンテナパッケージング、構造化ログとログベースアラートによるメール通知、Cloud Scheduler による定期実行、最小限のデプロイスクリプトと手順書、Broker 経由の pytest `cloud` テストと `e2e_cloud` ローカル E2E。
- Out of scope: ポート契約・抽出スキーマ・アプリレベルの状態遷移（extraction-pipeline が所有）、命名規則・状態プレフィックスの定義（core-naming-engine が所有）、Broker API の形状（gcp-test-broker が所有。拡張が必要な場合は同スペックへの変更要求として記録する）、Drive プッシュ通知、Firestore 等の外部ステートストア、Gmail API による直接送信、Terraform/IaC の本格整備、複数文書 PDF の分割、実 Google API に対する DevContainer からの自動 E2E（Broker の実 API 仲介拡張後の将来スコープ）。
- Adjacent expectations: extraction-pipeline のポート契約（`DrivePort` / `OcrPort` / `ExtractionPort`、`PortError` 派生の失敗表現）、抽出スキーマ（`DocumentExtraction`）、処理結果要約（`RunSummary` / `FileOutcome`）、確定版プロンプト素材を消費する（変更しない）。gcp-test-broker v0 のフィクスチャ API（`GET /health`、`POST /ocr-fixture`、`POST /extract-fixture`）を消費する。secret-scanning（gitleaks）は隣接する防御層であり、本機能はデプロイ関連ファイル・ログ・テストコードに認証情報を含めない設計でこれを補完する。

## Requirements

### Requirement 1: Google Drive 実アダプタ

**Objective:** 運用者として、監視フォルダ（`/From_BrotherDevice`）上の実ファイルを一覧・取得・リネームできる実アダプタがほしい。フェイクで検証済みのパイプラインを実際の Drive に接続するためである。

#### Acceptance Criteria

1. When 監視フォルダの一覧取得が要求されたとき, the Drive 実アダプタ shall 監視フォルダ直下のファイルのみ（サブフォルダの中身・ゴミ箱内のファイルを含めない）を、安定した識別子と名前の組として全件返す。
2. When ファイル内容の取得が要求されたとき, the Drive 実アダプタ shall 当該ファイルの PDF 内容をそのまま返す。
3. When リネームが要求されたとき, the Drive 実アダプタ shall 当該ファイルの名前のみを変更する（内容・格納場所・その他の属性を変更しない）。
4. If Google Drive の呼び出しが失敗したとき, then the Drive 実アダプタ shall ポート契約が定める Drive 系の失敗として報告する（基盤 SDK の例外をそのまま漏らさない）。
5. The Drive 実アダプタ shall 本番実行時のサービスアイデンティティ（サービスアカウント）で認証し、サービスアカウントキーのファイルを使用しない。

### Requirement 2: Document AI OCR 実アダプタ

**Objective:** 運用者として、スキャン PDF から実際に全文テキストを取得できる OCR 実アダプタがほしい。実文書に対する抽出・命名を成立させるためである。

#### Acceptance Criteria

1. When PDF 内容の OCR が要求されたとき, the OCR 実アダプタ shall Document AI で認識した全文テキストをポート契約の OCR 結果として返す。
2. If 文書からテキストが検出されなかったとき, then the OCR 実アダプタ shall 空テキストの正常応答を返す（失敗として扱わない）。
3. If Document AI の呼び出しが失敗したとき, then the OCR 実アダプタ shall ポート契約が定める OCR 系の失敗として報告する。

### Requirement 3: Gemini 構造化抽出実アダプタ

**Objective:** 運用者として、OCR テキストから実際に構造化メタデータを抽出できる LLM 実アダプタがほしい。文書内容に基づく自動命名を実現するためである。

#### Acceptance Criteria

1. When OCR テキストからの構造化抽出が要求されたとき, the 抽出実アダプタ shall 確定版プロンプト素材（抽出ポリシー・命名ポリシー）を用いて Gemini に構造化出力を要求し、抽出メタデータを返す。
2. The 抽出実アダプタが返す抽出メタデータ shall 抽出スキーマの不変条件（信頼度は 0 から 1、期間種別ごとの必須項目、読み取れないフィールドは欠落として明示）を満たす。
3. If Gemini の応答が抽出スキーマに適合しないとき, then the 抽出実アダプタ shall 限定された回数の再要求を行い、それでも適合しない場合は抽出系の失敗として報告する。
4. The 抽出実アダプタ shall OCR テキストとプロンプト素材以外の情報（認証情報・環境変数等）を LLM への要求に含めない。

### Requirement 4: インフラレベルのリトライ戦略と冪等性

**Objective:** 運用者として、一時的な API 障害で不要なエラー遷移が起きず、再試行・再実行によって二重リネームや二重課金が発生しないことを保証してほしい。無人運用を安全に成立させるためである。

#### Acceptance Criteria

1. If 外部 API の呼び出しが一時的エラー（レート制限・サーバ内部エラー・タイムアウト）で失敗したとき, then the 実アダプタ shall 上限回数付きの間隔を空けた再試行を行う。
2. If 再試行の上限まで失敗が続いたとき, then the 実アダプタ shall 対応するポート契約の失敗として報告する（当該ファイルのエラー遷移はアプリケーション層に委ねる）。
3. If 恒久的エラー（認証・権限・不正要求）で失敗したとき, then the 実アダプタ shall 再試行せずに直ちに失敗として報告する。
4. The システム shall 同一ファイルへの処理・リネームが再試行・再実行で繰り返されても、最終的な Drive 上の結果が変わらないこと（二重リネーム・多重サフィックスが生じないこと）を、ファイル名による状態表現の下で保証する。
5. The ジョブ実行 shall 定期実行の間隔を超えて実行し続けない構成とし、実行同士の重なりを防ぐ。
6. If ジョブの起動時処理（実行時設定の読み込み・プロンプト素材の読み込み・監視フォルダの一覧取得）が失敗したとき, then the ジョブ shall 当該実行を失敗として終了し、同一実行の自動再試行を行わない（次回の定期実行に委ねる）。

### Requirement 5: Cloud Run Job パッケージングとエントリポイント

**Objective:** 運用者として、パイプラインを単発バッチとして実行できるコンテナイメージとエントリポイントがほしい。Cloud Run Job 上での定期実行を成立させるためである。

#### Acceptance Criteria

1. The ジョブ shall コンテナイメージとしてパッケージングされ、1 回の起動でパイプラインを 1 回実行して終了する。
2. The エントリポイント shall 実行時設定（対象フォルダ・信頼度しきい値・接続先情報等）を環境変数から読み込み、必須設定が欠落しているときは起動を失敗させる。
3. The コンテナイメージ shall 確定版プロンプト素材を同梱し、エントリポイントが実行時にそれを読み込む。
4. When パイプラインが完走したとき（ファイル単位の要確認・エラーを含む）, the ジョブ shall 正常終了する。
5. If 起動時失敗（設定不備・プロンプト素材欠落・一覧取得失敗）が発生したとき, then the ジョブ shall 異常終了し、原因が判別できるログを残す。
6. The コンテナイメージおよびリポジトリ内のデプロイ関連ファイル shall 認証情報・サービスアカウントキー・トークンを含まない。

### Requirement 6: 構造化ログと監視・メール通知

**Objective:** 運用者として、要確認・エラーの発生をメールで受け取り、処理の履歴を機械可読なログで追跡したい。Drive を常時監視しなくても対応が必要な事象に気付けるようにするためである。

#### Acceptance Criteria

1. The ジョブ shall 実行の開始・ファイルごとの処理結果・実行全体の要約を構造化ログ（機械可読な形式）として出力する。
2. When ファイルが要確認状態へ遷移したとき, the ジョブ shall 要確認を表す構造化ログイベントを警告レベルで出力する（対象ファイル名と理由を含む）。
3. When ファイルがエラー状態へ遷移したとき、または起動時失敗が発生したとき, the ジョブ shall エラーを表す構造化ログイベントをエラーレベルで出力する（対象ファイル名または失敗原因の要約を含む）。
4. The 監視構成 shall 要確認・エラーの構造化ログイベントを検知し、fumiaki.k@gmail.com へメール通知を送る。
5. The 監視構成 shall 全ファイルが成功またはスキップのみの実行では通知を発生させない。
6. The 構造化ログ shall 認証情報・アクセストークン・Authorization ヘッダー値・環境変数のダンプ・OCR 全文・PDF 内容を含めない。

### Requirement 7: 定期実行とデプロイ手順

**Objective:** 運用者として、5 分ごとの自動実行と、再現可能な最小限のデプロイ手順がほしい。手作業に依存せずシステムを稼働・再構築できるようにするためである。

#### Acceptance Criteria

1. The システム shall 5 分ごとにジョブを起動する定期実行を構成する。
2. The ジョブ shall 必要最小限の権限を持つ専用のサービスアカウントで実行される。
3. The デプロイ shall リポジトリ内の最小限のスクリプトと手順書により再現可能である（Terraform 等の IaC 本格整備は将来 PBI とする）。
4. The 手順書 shall デプロイ後の動作確認手順（ジョブの手動実行、ログ・メール通知の確認）と、要確認・エラーファイルの手動リトライ運用（ファイル名をスキャナー生成名に戻す）を含む。
5. The デプロイ手順 shall 監視フォルダへのアクセス権付与（サービスアカウントへのフォルダ共有）を含み、それ以外の Drive 全体へのアクセスを要求しない。

### Requirement 8: Broker 経由のクラウド統合テスト

**Objective:** 開発者として、DevContainer 内から Broker 経由でアダプタ層のクラウド統合テストを実行したい。Google API を直接呼ばずに、Broker 応答とポート契約の適合を自動検証するためである。

#### Acceptance Criteria

1. The クラウド統合テスト shall pytest `cloud` マーカーで分類され、デフォルトのローカルテスト実行から除外される。
2. When `cloud` マーカーのテストを明示的に実行したとき, the テストスイート shall Broker のフィクスチャ応答をポート契約の型（OCR 結果・抽出メタデータ）へ変換してパイプラインに供給できるテスト用アダプタの動作を検証する。
3. If Broker がエラー応答（未知ケース・不正要求）を返したとき, then the テスト用アダプタ shall ポート契約が定める対応する失敗として報告する。
4. The クラウド統合テスト shall DevContainer から Broker 以外の外部サービス（Google API を含む）へ接続しない。
5. If テストの実現に Broker API の拡張が必要になったとき, then 本機能 shall Broker API を独自に定義せず、gcp-test-broker スペックへの変更要求として記録する。

### Requirement 9: Broker 経由のローカル E2E

**Objective:** 開発者として、デプロイ前にジョブのフロー全体を Broker 経由でローカルに 1 回通す E2E 検証がほしい。実サービス接続前に、検出からリネーム・ログ出力までの結合を確認するためである。

#### Acceptance Criteria

1. The ローカル E2E テスト shall pytest `e2e_cloud` マーカーで分類され、デフォルトのローカルテスト実行から除外される。
2. When `e2e_cloud` マーカーのテストを明示的に実行したとき, the テストスイート shall Broker のフィクスチャを用いてパイプライン全体（検出 → OCR → 抽出 → 命名 → リネーム → 状態遷移 → 要約）を 1 回通し、合意済み代表 3 文書例が期待どおりの最終ファイル名にリネームされることを検証する。
3. The ローカル E2E shall 低信頼度ケースが要確認状態へ遷移し、要確認を表す構造化ログイベントが出力されることを検証する。
4. The ローカル E2E shall 処理済み状態のファイルが再実行で再処理されないこと（冪等性）を検証する。
5. The ローカル E2E shall 実 Google API を呼び出さない（Broker のみと通信する）。
