# Implementation Plan

前提: 上流スペック core-naming-engine / extraction-pipeline / gcp-test-broker が実装済みであること（`scanner_rename.domain` / `ports` / `extraction` / `app` の公開 API、確定版 `app_llm_prompts/`、Broker v0 とサンプルフィクスチャ、`tests/cloud/conftest.py`）。

- [ ] 1. ランタイム依存とテスト分類の基盤を整備する
  - `pyproject.toml` の `[project].dependencies` に `google-api-python-client` / `google-auth` / `google-cloud-documentai` / `google-genai` を追加し、ロックを更新する
  - `e2e_cloud` マーカーの説明を「Broker 経由でジョブ全体を通す E2E」の実態に合わせて更新する（デフォルト実行から除外される既存の `addopts` は変更しない）
  - 観察可能な完了条件: `uv sync` が成功し、デフォルトの `uv run pytest` が外部サービスなしでグリーンのまま、`cloud` / `e2e_cloud` が収集されない
  - _Requirements: 8.1, 9.1_

- [ ] 2. 共通リトライヘルパを実装する
  - 例外分類関数を注入できる上限付き指数バックオフ（フルジッタ・遅延上限・sleep 注入）を実装する
  - 一時的エラーのみ再試行し、恒久的エラーは即時再送出、上限到達時は最後の例外を送出する
  - 観察可能な完了条件: 単体テストで再試行回数・バックオフ列（sleep 引数）・恒久的エラーの非再試行・上限時の例外送出が固定される
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 3. 実アダプタ 3 種を実装する
- [ ] 3.1 (P) Google Drive 実アダプタを実装する
  - 監視フォルダ直下のみの一覧（ゴミ箱・サブフォルダ除外、ページネーション全消化）、PDF 取得、名前のみのリネームを実装する
  - SDK 例外を Drive 系の失敗へ変換し、403 のレート系 reason を一時的エラーとして再試行、権限系は即時失敗にする
  - 認証は ADC 前提とし、キーファイルを扱うコード経路を持たない
  - 観察可能な完了条件: スタブ SDK の単体テストで一覧クエリ・写像・エラー分類・リネーム送信ボディ（名前のみ）が固定され、Pyright がポート適合を検証する
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3, 4.4_
  - _Boundary: adapters/google_drive_

- [ ] 3.2 (P) Document AI OCR 実アダプタを実装する
  - PDF バイト列を同期処理にかけ、全文テキストをポート契約の OCR 結果として返す（テキスト未検出は空文字列の正常応答）
  - 失敗を OCR 系の失敗へ変換し、一時的エラーは共通リトライで再試行する
  - 観察可能な完了条件: スタブクライアントの単体テストで正常・空文書・一時的/恒久的エラーの各挙動が固定される
  - _Requirements: 2.1, 2.2, 2.3, 4.1, 4.2, 4.3_
  - _Boundary: adapters/document_ai_

- [ ] 3.3 (P) Gemini 構造化抽出実アダプタを実装する
  - 抽出スキーマを鏡写しにした response schema 定数を定義し、確定版プロンプト素材（抽出 + 命名ポリシー）を system instruction、OCR テキストのみを user content とする要求を組み立てる
  - 応答 JSON を上流の抽出スキーマ型へ構築し、不変条件違反・JSON 破損は 1 回だけ再要求してから抽出系の失敗にする。通信レベルの一時的エラーは共通リトライで扱う
  - 観察可能な完了条件: 単体テストで schema 定数と上流スキーマのフィールド一致、期間 3 種を含む正常パース、不適合 → 再要求 → 失敗の流れ、要求ペイロードに OCR テキストとプロンプト以外が含まれないことが固定される
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3_
  - _Boundary: adapters/gemini_

- [ ] 4. ランタイム層（設定・ログ・エントリポイント）を実装する
- [ ] 4.1 (P) 実行時設定の環境変数契約を実装する
  - design の環境変数表（必須 4 + 任意 4、既定値）どおりに解決し、必須欠落・数値不正・しきい値範囲外は設定エラーで即時失敗させる
  - 観察可能な完了条件: 単体テストで必須欠落 → 失敗、既定値解決、範囲検証が固定され、エラーメッセージが変数名のみを示す（値をダンプしない）
  - _Requirements: 5.2_
  - _Boundary: runtime/config_

- [ ] 4.2 (P) 構造化ログのイベント出力を実装する
  - design のイベント表（run_started / file_processed / attention_required / run_completed / job_failed）を 1 行 JSON + `severity` で stdout に出力する
  - 要確認は WARNING、エラー・起動時失敗は ERROR とし、許可フィールドのみを出力する（認証情報・OCR 全文・PDF 内容を表現するフィールドを持たない）
  - 観察可能な完了条件: 単体テストで各イベントの JSON 形状と severity、attention_required が `docs/security-notes.md` の合意例（event / status / file_name / reason / severity）と一致することが固定される
  - _Requirements: 6.1, 6.2, 6.3, 6.6_
  - _Boundary: runtime/logging_

- [ ] 4.3 エントリポイント（合成ルート）を実装する
  - 設定 → プロンプト素材 → SDK クライアント + 実アダプタ 3 種 → パイプライン、の順で組み立てて 1 回実行し、処理結果要約を全件ログイベント化する
  - 完走時（要確認・エラー混在を含む）は正常終了、起動時失敗（設定・プロンプト・クライアント構築・一覧取得）は job_failed イベント + 異常終了とし、合成済み依存を注入できる構造にする
  - 観察可能な完了条件: フェイク注入の単体テストで exit 0 / exit 1 の分岐とイベント発火順序が固定され、`python -m scanner_rename.runtime.main` が起動できる
  - _Depends: 3.1, 3.2, 3.3, 4.1, 4.2_
  - _Requirements: 4.6, 5.1, 5.4, 5.5_

- [ ] 5. コンテナイメージをパッケージングする
  - `python:3.13-slim` + uv の 2 ステージ Dockerfile を作成し、`src/scanner_rename` と確定版 `app_llm_prompts/` を同梱、非 root でエントリポイントを起動する
  - ビルドコンテキストに認証情報・キー類が入らない構成にする（COPY 対象をソース・プロンプト・依存定義に限定）
  - 観察可能な完了条件: ローカルで `docker build` が成功し、必須環境変数なしの `docker run` が job_failed イベントを出して exit 1 で終了する
  - _Requirements: 5.1, 5.3, 5.6_

- [ ] 6. デプロイ・監視・定期実行の構成を作成する
- [ ] 6.1 (P) GCP セットアップとジョブデプロイのスクリプトを作成する
  - 初回セットアップ（API 有効化、実行/起動 SA 作成、最小ロール付与、Document AI プロセッサ作成、フォルダ共有用に実行 SA メールを表示）を冪等なスクリプトにする
  - ジョブデプロイ（イメージビルド、環境変数一式、`--max-retries=0`、`--task-timeout=240s`、実行 SA 指定）をスクリプトにする
  - 観察可能な完了条件: `bash -n` が通り、スクリプトにシークレット値の埋め込みがなく、プロジェクト ID 等は引数/環境変数で受け取る
  - _Requirements: 4.5, 4.6, 5.6, 7.2, 7.3_
  - _Boundary: deploy/setup_gcp.sh, deploy/deploy_job.sh_

- [ ] 6.2 (P) 監視・メール通知の構成スクリプトを作成する
  - fumiaki.k@gmail.com のメール通知チャネルと、ログ一致アラートポリシー 2 件（needs_review = attention_required かつ status=needs_review、error = severity>=ERROR の attention_required または job_failed）を作成するスクリプトにする
  - 成功・スキップのイベントがどのフィルタにも一致しないことをフィルタ定義で保証する
  - 観察可能な完了条件: `bash -n` が通り、フィルタ文字列が runtime/logging のイベント表（event / status / severity）と一致する
  - _Requirements: 6.4, 6.5_
  - _Boundary: deploy/setup_monitoring.sh_

- [ ] 6.3 (P) 定期実行の構成スクリプトを作成する
  - Cloud Scheduler ジョブ（`*/5 * * * *`）が起動用 SA の OAuth トークンで Cloud Run Jobs の実行エンドポイントを呼ぶ構成をスクリプトにする
  - 観察可能な完了条件: `bash -n` が通り、スケジュール式が 5 分間隔、認可が起動用 SA 経由である
  - _Requirements: 7.1_
  - _Boundary: deploy/setup_scheduler.sh_

- [ ] 6.4 デプロイ手順書（runbook）を作成する
  - 前提 → フォルダ ID 取得と実行 SA への監視フォルダ共有 → スクリプト実行順 → スモーク確認（テスト PDF 投入、手動ジョブ実行、リネーム・ログ・メール確認）→ 手動リトライ運用（状態プレフィックス名をスキャナー生成名に戻す）→ 制約（間隔とタイムアウトの関係、実 API 自動 E2E は Broker 拡張後の将来 PBI）の構成で書く
  - Broker v0 に不足する実 API 仲介エンドポイントを gcp-test-broker への変更要求として明記する
  - 観察可能な完了条件: `deploy/runbook.md` が上記の全節を持ち、`.claude/rules/markdown-style.md`（WHY 中心、コマンド詳細はスクリプト参照）に従っている
  - _Requirements: 7.3, 7.4, 7.5, 8.5_

- [ ] 7. Broker 経由のクラウド統合テストを実装する
  - `OcrPort` / `ExtractionPort` を Broker フィクスチャで実装するテスト用アダプタを `tests/cloud/` に作る（擬似 PDF 内容からの case_id 解決、OCR テキスト → case_id 対応表、応答 → 上流 DTO 変換、Broker エラー → ポート契約の失敗変換）
  - サンプル 4 ケースの契約適合（不変条件通過）と未知 case_id の失敗変換を `cloud` マーカーのテストで検証する。HTTP は標準ライブラリのみ、既存 conftest のプリフライトを再利用する
  - 観察可能な完了条件: Broker 起動下で `uv run pytest -m cloud tests/cloud` がグリーン、デフォルト実行では収集されない
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  - _Depends: 1_
  - _Boundary: tests/cloud broker_adapters（conftest.py は gcp-test-broker 所有・変更しない）_

- [ ] 8. Broker 経由のローカル E2E を実装する
  - 上流のフェイク Drive にスキャナー生成名の 4 ファイル（高信頼 3 + 低信頼 1）を投入し、テスト用 Broker アダプタでパイプライン全体を 1 回実行する `e2e_cloud` テストを作る
  - 合意済み 3 文書例の最終名完全一致、低信頼ケースの要確認遷移と attention_required（WARNING）イベント出力、2 回目実行での全件スキップ（冪等性）を検証する
  - 実 Google API・実アダプタをこのテストから import しない
  - 観察可能な完了条件: Broker 起動下で `uv run pytest -m e2e_cloud tests/e2e_cloud` がグリーン
  - _Requirements: 4.4, 9.1, 9.2, 9.3, 9.4, 9.5_
  - _Depends: 4.2, 7_
  - _Boundary: tests/e2e_cloud_

- [ ] 9. 全体整合を検証する
  - デフォルトのローカルテスト（`unit` + `integration_fake`）、Ruff、Pyright が全件グリーンであることを確認する
  - `tests/README.md` に `cloud` / `e2e_cloud` の実行前提（Broker 起動・環境変数）の本スペック分を追記する
  - 観察可能な完了条件: 上記チェック一式のコマンド実行結果がすべて成功し、Broker 起動下で `cloud` / `e2e_cloud` の実行手順が README どおりに再現できる
  - _Requirements: 8.1, 8.4, 9.1, 9.5_
