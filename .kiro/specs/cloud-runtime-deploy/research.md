# Research & Design Decisions: cloud-runtime-deploy

## Summary

- **Feature**: `cloud-runtime-deploy`
- **Discovery Scope**: Extension（既存ポート契約への実アダプタ追加）+ Complex Integration（GCP ランタイム統合）
- **Key Findings**:
  - 上流契約は完全に固定済み: `DrivePort` / `OcrPort` / `ExtractionPort` と `PortError` 派生、`DocumentExtraction`、`RunSummary` / `FileOutcome`（extraction-pipeline design.md）。本スペックは実装側であり契約を再定義しない
  - Broker v0 はフィクスチャ供給のみ（`/health`、`/ocr-fixture`、`/extract-fixture`）。実 Google API の仲介エンドポイントは存在しないため、DevContainer からの実サービス自動検証は v1 では不可能。実サービス検証はデプロイ後スモーク実行（運用者手順）で行う
  - 冪等性は上流の設計で大部分が担保済み: 処理対象判定がファイル名分類（`SCANNER_NEW` のみ）に基づくため、遷移済みファイルは再実行で再処理されない。本スペックが追加で保証すべきは (a) リネーム再試行の安全性、(b) 実行の重なり防止、(c) ジョブレベル再試行の抑制

## Research Log

### Google API クライアントの選定

- **Context**: 実アダプタ 3 種のランタイム依存を確定する必要がある（現状 `pyproject.toml` の runtime dependencies は空）
- **Sources Consulted**: Google Cloud 公式クライアントライブラリ体系、google-genai SDK 移行ガイド（既知知識。バージョン下限は実装時に `uv add` で最新安定版を確認する）
- **Findings**:
  - Drive API v3 には公式の専用クラウドクライアントがなく、`google-api-python-client`（discovery ベース）+ `google-auth`（ADC）が標準
  - Document AI は `google-cloud-documentai`（gapic クライアント、`process_document` に `raw_document` で PDF バイト列を渡せる）
  - Gemini は `google-genai`（統合 SDK）。`vertexai=True` + project/location 指定で Vertex AI バックエンドを使い、サービスアカウント（ADC）で認証できる — API キー不要でセキュリティ方針（キー不使用）に整合。旧 `google-generativeai` は非推奨
- **Implications**: runtime dependencies に `google-api-python-client` / `google-auth` / `google-cloud-documentai` / `google-genai` を追加。単体テストは SDK 境界をスタブ化しネットワーク不要を維持

### Drive API のフォルダスコープとレート制限

- **Context**: `DrivePort` の「監視フォルダ直下のみ」「安定 ID」の契約と、サービスアカウントでのアクセス方法
- **Findings**:
  - サービスアカウントは Drive の IAM ロールでは監視フォルダへ到達できない。運用者が `/From_BrotherDevice` フォルダをサービスアカウントのメールアドレスに編集者権限で共有する（デプロイ手順に含める）
  - 一覧は `files.list` + クエリ `'<folderId>' in parents and trashed = false and mimeType != 'application/vnd.google-apps.folder'`、`fields` を `files(id, name)` に絞り、ページネーションを全消化する。フォルダ ID は環境変数で与える（名前解決の曖昧性を避ける）
  - リネームは `files.update(fileId, body={"name": ...})`。file_id 指定で名前を確定値に置き換えるため、同じ要求の再送は同じ結果になる（自然に冪等）
  - Drive API のレート制限は HTTP 429 のほか、403 + reason `userRateLimitExceeded` / `rateLimitExceeded` で返る歴史的挙動がある。リトライ分類は 403 の reason を見る必要がある
- **Implications**: アダプタ構築時にフォルダ ID を注入。リトライ分類器は Drive 固有（403 rate 系を一時的エラー扱い）

### Gemini 構造化出力の方式

- **Context**: `DocumentExtraction` に適合する応答を安定して得る方法
- **Findings**:
  - `google-genai` の `response_mime_type="application/json"` + `response_schema` で構造化出力を強制できる。スキーマは JSON Schema 相当の辞書で与え、nullable なサブオブジェクト・enum（期間種別）・数値範囲を表現できる
  - スキーマ強制でも、必須項目間の整合（期間種別ごとの必須フィールド等）まで保証されるわけではない。frozen dataclass の `__post_init__` 検証（上流所有）を最終ゲートとし、不適合は限定回数の再要求後に `ExtractionError` とする
  - プロンプトは system instruction に確定版 `extraction_policy.md` + `naming_policy.md` を連結し、user content に OCR テキストのみを渡す（認証情報等を含めない構造的保証）
- **Implications**: response schema はアダプタ内で `DocumentExtraction` のフィールド構成から一元定義。スキーマ不適合の再要求は 1 回（計 2 試行）に限定

### Cloud Run Job の再試行・重なり・アラート経路

- **Context**: brief の「Cloud Run Job の再試行との整合」「5 分ごと実行」「ログベースアラート」
- **Findings**:
  - Cloud Run Job の `max-retries` はタスク失敗時にコンテナ全体を再実行する。起動時失敗（設定不備・権限不足）は数分内の再実行で直らないため `--max-retries=0` とし、次回の定期実行（5 分後）に委ねるのが最小で安全（OCR/LLM の再課金も抑制）
  - Scheduler は前回実行の完了を待たずに次を起動しうる。タスクタイムアウトを間隔未満（240 秒）に設定して実行の重なりを構造的に防ぐ。想定処理時間は数十秒であり 240 秒は十分
  - Cloud Logging は stdout の JSON 1 行を `jsonPayload` として解釈し、`severity` フィールドをログレベルとして扱う。専用のロギングクライアントライブラリは不要
  - Cloud Monitoring はログベースメトリクスを介さない「ログ一致条件のアラートポリシー」を直接サポートする。要確認（WARNING）とエラー（ERROR）の 2 ポリシー + メール通知チャネルで要件を満たせる
- **Implications**: 通知経路は 構造化ログ → Cloud Logging → ログ一致アラートポリシー → メールチャネル。成功時はどのフィルタにも一致しないため通知されない（6.5 が構成的に成立）

### Broker 経由テストの成立範囲

- **Context**: brief は「pytest `cloud` / `e2e_cloud` テストが Broker 経由で動作」を求めるが、Broker v0 はフィクスチャ供給のみ
- **Findings**:
  - Broker v0 の 3 エンドポイントで成立するのは (a) フィクスチャ応答 → ポート DTO 変換を担うテスト用アダプタの検証（`cloud`）、(b) テスト用アダプタ + インメモリ Drive（上流のフェイク）でパイプライン全体を通すローカル E2E（`e2e_cloud`）
  - 実 Google API を実アダプタで叩く自動テストは、`docs/security-notes.md` の許可方向（`/drive/list-test-files` 等 + 実 OCR/抽出仲介）を Broker が実装しない限り DevContainer から実行できない
- **Implications**: `e2e_cloud` マーカーの説明文を「Broker 経由でジョブ全体を通す E2E（将来: 実 GCP 仲介）」に更新する。実 API 仲介エンドポイントの追加は gcp-test-broker への変更要求として記録し（8.5）、v1 の実サービス検証はデプロイ後スモーク実行の手順書で担う

## Architecture Pattern Evaluation

| Option                                       | Description                                           | Strengths                      | Risks / Limitations                                | Notes                                      |
| -------------------------------------------- | ----------------------------------------------------- | ------------------------------ | -------------------------------------------------- | ------------------------------------------ |
| ヘキサゴナル継承 + 合成ルート（採用）        | 実アダプタは既存ポートの実装、`runtime/` が合成・実行 | 上流設計に完全整合、テスト容易 | なし（既定路線）                                   | steering / extraction-pipeline 設計に準拠  |
| アダプタ内に独自リトライなし（SDK 既定利用） | google-api-core / discovery の内蔵リトライに依存      | コード最小                     | 3 SDK で挙動・分類が不統一、Drive 403 rate 未対応  | 却下: 挙動の予測可能性を優先               |
| tenacity 等のリトライライブラリ採用          | 汎用リトライデコレータ                                | 実績豊富                       | 依存追加に対し要件が小さい（分類 + 上限 + jitter） | 却下: 標準ライブラリの小さなヘルパで足りる |

## Design Decisions

### Decision: リトライは共通ヘルパ 1 つに集約し、分類器をアダプタごとに注入する

- **Context**: 4.1–4.3 の一時的/恒久的エラーの区別と再試行を 3 アダプタで一貫させたい
- **Alternatives Considered**:
  1. SDK ごとの内蔵リトライ設定 — 挙動が不統一、テスト困難
  2. アダプタごとに個別実装 — 重複、ポリシー乖離のリスク
- **Selected Approach**: `adapters/retry.py` に `RetryPolicy`（frozen dataclass）と `execute_with_retry(fn, is_transient, policy)` を実装。指数バックオフ + ジッタ + 上限回数。sleep 関数を注入可能にして単体テストを決定論化
- **Rationale**: 分類（何が一時的か）は API ごとに違うが、再試行の機構は 1 つでよい
- **Trade-offs**: 自前実装の保守が必要だが、要件が小さく安定している
- **Follow-up**: 各 SDK の例外型 → 一時的/恒久的の分類表を単体テストで固定する

### Decision: ジョブは per-file エラーがあっても正常終了し、失敗通知はログイベントで行う

- **Context**: Cloud Run Job の失敗ステータスと通知経路の整合（4.6, 5.4, 5.5, 6.3）
- **Alternatives Considered**:
  1. エラーファイルがあれば非ゼロ終了 — Scheduler/Job 側の失敗再試行と干渉し、二重処理・二重課金リスク
  2. 常にゼロ終了 — 起動時失敗が Job の実行履歴上「成功」に見えて診断性が落ちる
- **Selected Approach**: パイプラインが `RunSummary` を返せた実行は exit 0（ファイル単位の要確認・エラーは構造化ログイベントで通知）。起動時失敗（設定・プロンプト・一覧取得）のみ exit 1 + ERROR イベント。`--max-retries=0` でジョブレベル再実行を無効化
- **Rationale**: アプリレベルの障害分離（上流設計）とインフラレベルの再試行の責務を混ぜない。通知はログベースアラートに一元化
- **Trade-offs**: ジョブ実行履歴だけでは要確認・エラーの有無が分からない（ログ/メールで補う）

### Decision: `e2e_cloud` マーカーを「Broker 経由のジョブ全体 E2E」に割り当てる

- **Context**: 既存マーカー定義は「real GCP services」だが、DevContainer から実 GCP へ直接接続することは恒久的に禁止
- **Alternatives Considered**:
  1. ローカル E2E も `cloud` マーカーに含める — brief の「`cloud` / `e2e_cloud` が Broker 経由で動作」の区別が消える
  2. 実 GCP E2E を強行 — セキュリティ制約違反
- **Selected Approach**: `cloud` = アダプタ単位の Broker 契約テスト、`e2e_cloud` = Broker 経由でジョブ全体を 1 回通すローカル E2E。`pyproject.toml` のマーカー説明文を実態に合わせて更新。実 GCP の仲介付き E2E は Broker v1 拡張（gcp-test-broker への変更要求）後の将来 PBI
- **Rationale**: 両マーカーとも「Broker 起動が前提」という実行条件は同じで、デフォルト実行から除外される挙動も既存の `addopts` で維持される
- **Trade-offs**: v1 の `e2e_cloud` は実 GCP に触れない。実サービスの検証はデプロイ後スモーク（runbook）でカバー

### Decision: Broker 応答 → ポート DTO のテスト用アダプタは `tests/cloud/` に置く

- **Context**: ローカル E2E には `OcrPort` / `ExtractionPort` を Broker フィクスチャで実装するアダプタが必要
- **Alternatives Considered**:
  1. `src/scanner_rename/adapters/broker/` に本体実装 — 本番コードにテスト専用経路が混入する
- **Selected Approach**: `tests/cloud/broker_adapters.py` にテスト基盤として実装（gcp-test-broker が確立した「変換ヘルパは tests/cloud/ に閉じる」境界決定を踏襲・拡張）。PDF 内容に埋めた case 参照から `case_id` を解決し、OCR テキスト → `case_id` の対応は初期化時に全ケースの OCR フィクスチャを取得して構築する（決定論）
- **Rationale**: 本番の合成ルート（実アダプタのみ）と開発時テスト経路を構造的に分離。「Broker はローカル開発専用」の制約を import 構造で保証する
- **Trade-offs**: テストコードがやや厚くなるが、`src/` の純度を優先

### Decision: Drive フォルダはフォルダ ID の環境変数で指定する

- **Context**: `/From_BrotherDevice` というパス名からの解決は同名フォルダ・共有状態に依存して曖昧
- **Selected Approach**: `DRIVE_FOLDER_ID` を必須環境変数とし、ID の取得手順（URL からのコピー）と SA への共有手順を runbook に記載
- **Rationale**: fail fast（起動時検証）と決定論。名前解決ロジックの実装・テストを丸ごと省ける
- **Trade-offs**: 初回セットアップに手作業 1 ステップ増（許容）

## Risks & Mitigations

- Gemini モデルの世代交代でモデル名が失効する — モデル名を環境変数 `GEMINI_MODEL` にし、デプロイスクリプトの既定値だけ更新すればよい構成にする
- スキーマ強制でも LLM 出力が不変条件を破る — 上流 `__post_init__` を最終ゲートにし、1 回だけ再要求。それでも失敗なら `ExtractionError` → `rename_error_` 遷移（手動リトライ経路あり）
- Drive の 403 レート制限を恒久エラーと誤分類 — 403 の reason 判定を単体テストで固定
- Scheduler 起動と実行時間の競合（重なり） — タスクタイムアウト 240 秒 + 実測数十秒の処理時間で構造的に回避。将来ファイル数が増えたら間隔/タイムアウトを見直す（runbook に注意点として記載）
- サービスアカウントへのフォルダ共有漏れで一覧が空になり「成功」に見える — 一覧 0 件は正常だが、スモーク手順でテストファイル投入 → リネーム確認を必須化して検出する

## References

- `.kiro/specs/extraction-pipeline/design.md` — ポート契約・スキーマ・RunSummary（本スペックの上流契約）
- `.kiro/specs/gcp-test-broker/design.md` — Broker v0 API 契約・tests/cloud の既存構成
- `docs/security-notes.md` — 隔離モデル・Broker 許可方向・本番アイデンティティ・ログ禁止事項
- `docs/adr-candidates/`（ADR 0001–0005）— Cloud Run Job / ポーリング / ファイル名状態 / Broker / プロンプト管理の決定
- Google Drive API v3 `files.list` / `files.update`、Document AI `process_document`、google-genai 構造化出力 — 公式ドキュメント（バージョン・シグネチャは実装時に再確認）
