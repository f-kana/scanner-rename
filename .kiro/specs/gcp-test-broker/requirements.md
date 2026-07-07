# Requirements Document

## Project Description (Input)

Claude Code（DevContainer 内）にクラウド統合テストを実行・自己修正させたいが、セキュリティ方針により DevContainer から Google API を直接呼ぶことも、生の GCP 認証情報を Claude Code に扱わせることもできない。この隔離を成立させる仲介者がまだ存在しない（`broker/` は README のみ）。

Mac ホスト側（DevContainer の外）で動作する GCP Test Broker v0 を `broker/` に実装する。v0 はフィクスチャ供給に徹する: OCR フィクスチャと抽出フィクスチャを返す決定論的なエンドポイントを提供し、DevContainer 内の pytest `cloud` マーカーのテストから呼び出せるようにする。Broker は目的を絞った狭い API とし、生の Google API プロキシにはしない。認証情報・トークンをレスポンスやログに含めない。フィクスチャの形は extraction-pipeline が所有するポート契約・抽出スキーマに整合させ、Broker 経由でジョブフロー全体をローカルで 1 回通す E2E 動作確認の土台になる。

## Introduction

本機能 gcp-test-broker は、スキャン PDF 自動リネームシステムの開発を支えるホスト側テスト基盤である。DevContainer 内の Claude Code が生の GCP 認証情報に触れることなくクラウド統合テストを実行できるよう、Mac ホスト上で動作する小さな仲介サービス（GCP Test Broker）を提供する。v0 は決定論的なテストデータ（OCR フィクスチャ・抽出フィクスチャ）の供給に徹し、DevContainer 内のテストが `case_id` を指定してフィクスチャを取得できるようにする。Broker は `docs/security-notes.md` の隔離モデルを実装するセキュリティ境界そのものであり、狭い目的特化 API であること・認証情報を一切漏らさないことが本質的な要件である。

## Boundary Context

- In scope: Broker v0 本体（`broker/` に実装、Mac ホスト上で動作）、稼働確認と OCR・抽出フィクスチャ供給のエンドポイント、`case_id` による許可リストベースのフィクスチャ解決、DevContainer 内 pytest `cloud` マーカーのテストからの到達確認、ジョブフロー全体のローカル E2E を可能にする初期フィクスチャケース一式。
- Out of scope: 実 Google API の仲介エンドポイント（Document AI / Gemini / Drive の限定操作。v1 以降に消費者駆動で追加）、アプリケーション本体の実アダプタ（cloud-runtime-deploy が所有）、Broker 自体のクラウドデプロイ（Broker はローカル専用）、クラウド統合テストシナリオそのものの定義（cloud-runtime-deploy が消費者として所有）、ポート契約・抽出スキーマの変更（extraction-pipeline が所有）。
- Adjacent expectations: フィクスチャ応答の形は extraction-pipeline が定義するポート契約（OCR 結果・抽出メタデータ）に変換可能であることを本機能が保証する。`docs/security-notes.md` の隔離モデル（DevContainer は Google API を直接呼ばない、認証情報は Broker 側のみ）は本機能の変更不可能な前提である。secret-scanning（gitleaks）は隣接する防御層であり、本機能はレスポンス・ログに秘密を含めない設計でこれを補完する。

## Requirements

### Requirement 1: Broker サービスの提供と稼働確認

**Objective:** 開発者として、Mac ホスト上で起動でき、稼働状態を確認できる Broker サービスがほしい。クラウド統合テストの前提となる仲介者を確実に立ち上げ、問題を早期に検出できるようにするためである。

#### Acceptance Criteria

1. The Broker shall Mac ホスト上（DevContainer の外）で動作し、ホストのループバックアドレスでのみ要求を待ち受ける。
2. When 稼働確認要求を受けたとき, the Broker shall 稼働中であることを示す応答を返す（応答に認証情報・内部パス等の機微情報を含めない）。
3. If 起動時にフィクスチャ格納場所が存在しないか読み取れないとき, then the Broker shall 原因が分かる明示的なエラーで起動を失敗させる（不完全な状態で稼働し続けない）。
4. The Broker shall 起動手順（前提・設定値・起動コマンド）を `broker/` の文書で確認できるようにする。

### Requirement 2: OCR フィクスチャの供給

**Objective:** 開発者として、実 OCR サービスを呼ばずに既知の OCR 結果を取得したい。決定論的なテストデータでクラウド統合テストの再現性を確保するためである。

#### Acceptance Criteria

1. When `case_id` を指定した OCR フィクスチャ要求を受けたとき, the Broker shall 当該ケースに対応する OCR テキスト応答を返す。
2. The OCR フィクスチャ応答 shall アプリケーションが定義する OCR 結果の形（全文テキスト）に変換可能な内容とする。
3. When 同一の `case_id` で複数回要求したとき, the Broker shall 毎回同一の応答を返す。

### Requirement 3: 抽出フィクスチャの供給

**Objective:** 開発者として、実 LLM を呼ばずに既知の構造化抽出結果を取得したい。信頼度分岐を含むパイプラインの挙動を決定論的に検証するためである。

#### Acceptance Criteria

1. When `case_id` を指定した抽出フィクスチャ要求を受けたとき, the Broker shall 当該ケースに対応する抽出メタデータ（文書日付・元号シグナル・書類タイトル・発行元・文書種別・期間・フィールドごとの信頼度とエビデンス・判断理由）を返す。
2. The 抽出フィクスチャ応答 shall アプリケーションが定義する抽出メタデータの制約（信頼度は 0 から 1、期間種別ごとの必須項目、読み取れないフィールドは欠落として明示）を満たす内容とする。
3. When 同一の `case_id` で複数回要求したとき, the Broker shall 毎回同一の応答を返す。
4. The 抽出フィクスチャ shall 高信頼度（命名可能）と低信頼度（要確認相当）の両方のケースを表現できる。

### Requirement 4: case_id によるフィクスチャ解決

**Objective:** 開発者（および運用者）として、DevContainer 側からは `case_id` という識別子だけでフィクスチャを参照したい。DevContainer 内のコードが任意のホストファイルを読み取らせる経路を作らないためである。

#### Acceptance Criteria

1. The Broker shall フィクスチャを事前に定義された `case_id` の一覧（許可リスト）に対してのみ解決し、要求側からファイルパスを指定させない。
2. If 未定義の `case_id` が指定されたとき, then the Broker shall 当該ケースが存在しないことが分かるエラー応答を返す（ホスト側のファイル構成等の内部情報を含めない）。
3. If `case_id` にパス区切り文字や親ディレクトリ参照などの識別子として不正な形式が含まれるとき, then the Broker shall 解決を試みず要求を拒否する。
4. The Broker shall フィクスチャ実体をリポジトリ外・DevContainer 外の格納場所から読み込めるようにする。

### Requirement 5: セキュリティ境界の維持

**Objective:** 運用者として、Broker が狭い目的特化 API であり続け、認証情報を一切露出しないことを保証してほしい。Claude Code に GCP 認証情報を渡さないという隔離モデルの根幹を守るためである。

#### Acceptance Criteria

1. The Broker shall 目的を定めたエンドポイントのみを公開し、任意の外部 API 要求を中継する汎用機能を持たない。
2. If 未定義のエンドポイントへの要求を受けたとき, then the Broker shall 中継や転送を行わずエラー応答を返す。
3. The Broker shall 応答に認証情報・アクセストークン・Authorization ヘッダー値を含めない。
4. The Broker shall ログに認証情報・アクセストークン・Authorization ヘッダー値を出力しない。
5. The Broker v0 shall Google API を呼び出さない（フィクスチャ供給のみを行う）。

### Requirement 6: DevContainer からの到達性とクラウドテスト統合

**Objective:** 開発者として、DevContainer 内の pytest から Broker を呼び出すクラウド統合テストを実行したい。Claude Code がクラウド統合テストを自律実行・自己修正できるようにするためである。

#### Acceptance Criteria

1. When DevContainer 内のテストが設定された Broker 接続先に要求を送ったとき, the クラウド統合テスト shall Broker の応答を受信できる。
2. The Broker を呼び出すテスト shall pytest `cloud` マーカーで分類され、デフォルトのローカルテスト実行から除外される。
3. When `cloud` マーカーのテストを明示的に実行したとき, the テストスイート shall Broker の OCR・抽出フィクスチャ応答をアプリケーションのポート契約の型へ変換できることを検証する。
4. If Broker に到達できないとき, then the クラウド統合テスト shall 到達不能が原因であることが分かる形で失敗する（無関係なエラーに見せない）。
5. The クラウド統合テスト shall Broker 以外の外部サービス（Google API を含む）へ直接接続しない。

### Requirement 7: ローカル E2E の土台となる初期フィクスチャケース

**Objective:** 開発者として、合意済みの代表文書例をカバーするフィクスチャケース一式がほしい。Broker 経由でジョブフロー全体（検出 → OCR → 抽出 → 命名 → リネーム）をローカルで 1 回通す E2E 動作確認の土台にするためである。

#### Acceptance Criteria

1. The 初期フィクスチャケース shall 合意済みの代表 3 文書例（住宅ローン残高証明書・確定申告書・医療費通知）に対応する OCR・抽出フィクスチャの組を含む。
2. The 初期フィクスチャケース shall 低信頼度（要確認相当）を表すケースを少なくとも 1 つ含む。
3. The 各フィクスチャケース shall OCR 応答と抽出応答が同一文書として整合する内容を持つ（OCR テキストに抽出結果の根拠が含まれる）。
4. The 初期フィクスチャケース shall 参照用のサンプル一式としてリポジトリ内にも保持され、ホスト側格納場所へ配置する手順が文書化される。
