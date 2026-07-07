# Research & Design Decisions: gcp-test-broker

## Summary

- **Feature**: `gcp-test-broker`
- **Discovery Scope**: New Feature（ただし境界・隔離モデルは `docs/security-notes.md` / ADR 0004 / broker/README.md で事前確定済みのため、light discovery で十分と判断）
- **Key Findings**:
  - Broker v0 はフィクスチャ供給のみで Google API を一切呼ばないため、GCP 認証情報をプロセス内に持つ必要すらない（v0 の認証情報漏洩リスクは構造的にゼロにできる）
  - フィクスチャ応答の形は extraction-pipeline の `OcrResult` / `DocumentExtraction`（frozen dataclass、不変条件付き）に変換可能であることが契約。変換の正当性検証は DevContainer 側 `cloud` テストで実際に型を構築して行える
  - Docker Desktop for Mac では、ホストの 127.0.0.1 にバインドしたサービスへコンテナから `host.docker.internal` で到達できる（loopback バインドと DevContainer 到達性は両立する）

## Research Log

### Broker の実装スタック

- **Context**: `broker/` は README のみ。実装フレームワークが未確定
- **Sources Consulted**: `broker/README.md`（起動コマンドの概念例が `uv run uvicorn gcp_test_broker.main:app` を想定）、steering `tech.md`（Python + uv）、FastAPI / uvicorn 公式ドキュメント
- **Findings**:
  - README の概念例はすでに FastAPI/uvicorn 系の構成（`main:app`）を示している
  - FastAPI は Pydantic によるリクエスト/レスポンス検証を標準で持ち、「狭い API・厳格な入力検証」という本スペックの性格に合う
  - 標準ライブラリ `http.server` でも実装可能だが、ルーティング・検証・エラー応答の手書きが増え、コード量と欠陥リスクが上がる
- **Implications**: Broker は `broker/` 配下の独立 uv プロジェクトとし、FastAPI + uvicorn を採用する。アプリ本体（ルート `pyproject.toml`）のランタイム依存には影響しない

### DevContainer からホストへの到達性

- **Context**: 隔離モデルは「Broker はホストの 127.0.0.1:8765 でリッスン、DevContainer からホスト向けネットワークで到達」と定めている
- **Sources Consulted**: `docs/security-notes.md`、`broker/README.md`（`GCP_TEST_BROKER_URL=http://host.docker.internal:8765`）、Docker Desktop ネットワーキングの公知の挙動
- **Findings**:
  - Docker Desktop for Mac の `host.docker.internal` はホストの loopback で待ち受けるサービスに到達できる
  - 接続先はテスト側で環境変数 `GCP_TEST_BROKER_URL` から解決するのが README の既定路線
- **Implications**: Broker は 127.0.0.1 バインドを既定とし、DevContainer 側テストは `GCP_TEST_BROKER_URL`（既定値 `http://host.docker.internal:8765`）で接続する。0.0.0.0 バインドは不要（LAN 露出を避ける）

### フィクスチャ応答とポート契約の整合

- **Context**: フィクスチャの形は extraction-pipeline のポート契約・抽出スキーマ（上流所有）に整合させる必要がある
- **Sources Consulted**: `.kiro/specs/extraction-pipeline/design.md`（`OcrResult` / `DocumentExtraction` / `PortError` の定義、「gcp-test-broker のフィクスチャ応答は `OcrResult` / `DocumentExtraction` に変換可能な形とする（変換責務は cloud-runtime-deploy のアダプタ）」）
- **Findings**:
  - OCR 契約は `OcrResult(text: str)` のみ（v1 はレイアウト情報を扱わない）
  - 抽出契約は `DocumentExtraction`（`document_date` / `title` / `issuer` / `document_type` / `period` / `reason`、欠落は `None`、信頼度 0.0–1.0、期間は 3 種別の判別構造）で、不変条件は `__post_init__` が検証する
  - Broker 応答 JSON からポート DTO への「変換」を src/ 側の共有モジュールにすると、cloud-runtime-deploy が所有すべきアダプタ責務を先取りしてしまう
- **Implications**: Broker の応答 JSON は `DocumentExtraction` のフィールド構成をそのまま鏡写しにする（日付は ISO 8601 文字列、欠落フィールドは null）。変換可能性の検証は DevContainer 側 `cloud` テスト内のテストローカルなヘルパで実際に dataclass を構築して行い、本番用変換モジュールは作らない

### フィクスチャ格納と case_id 解決

- **Context**: `docs/security-notes.md` のフィクスチャポリシー（リポジトリ外格納、case_id → 許可リストのマッピング、任意パス参照の禁止）
- **Sources Consulted**: `docs/security-notes.md`、`broker/README.md`
- **Findings**:
  - Claude Code はフィクスチャをファイルパスではなく `case_id` で参照する。これは「DevContainer 側から任意のホストファイルを Google API に送らせない」ための設計であり、v0（フィクスチャ供給のみ）でも同じ入力面を維持しておくと v1 拡張時に API 形状が変わらない
  - 許可リストの実体は「`FIXTURE_DIR` 直下に存在するケースディレクトリの集合」で十分。`case_id` を厳格なパターン（`^[a-z0-9_]+$`）に制限すればパストラバーサルは構造的に不可能
- **Implications**: `FIXTURE_DIR/<case_id>/ocr.json` + `extraction.json` のレイアウトを採用。case_id はパターン検証 → ディレクトリ存在確認の 2 段階で解決する。リポジトリ内には配布用サンプル一式（`broker/sample_fixtures/`）を保持し、ホストへの配置手順を README に記す

## Architecture Pattern Evaluation

| Option                               | Description                                        | Strengths                                         | Risks / Limitations                                           | Notes                              |
| ------------------------------------ | -------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------- | ---------------------------------- |
| FastAPI + uvicorn（採用）            | 独立 uv プロジェクトとして小さな HTTP サービス     | 入出力検証が宣言的、README の既定路線、実装量最小 | 依存 2 件の追加（ただし Broker ローカル専用で本番に載らない） | 起動時検証・404 既定応答も標準機能 |
| 標準ライブラリ http.server           | 依存ゼロの手書きサーバ                             | 依存なし                                          | ルーティング・検証・エラー応答が手書きで欠陥リスク増          | 「洗練された手法」方針に反する     |
| アプリ本体パッケージに Broker を同居 | `src/scanner_rename/` 内に Broker モジュールを追加 | import 共有が容易                                 | 本番アプリに開発基盤が混入、依存境界が濁る                    | 不採用。ランタイムが別物           |

## Design Decisions

### Decision: Broker を `broker/` 配下の独立 uv プロジェクトにする

- **Context**: Broker は Mac ホスト上で動く別ランタイムであり、アプリ本体（Cloud Run Job）に同梱してはならない
- **Alternatives Considered**:
  1. ルートプロジェクトの optional dependency group として同居
  2. `broker/` 配下に独立した `pyproject.toml` を持つ uv プロジェクト
- **Selected Approach**: 2。パッケージ名 `gcp_test_broker`、依存は FastAPI + uvicorn のみ。Broker の単体テストは `broker/` 内で完結する
- **Rationale**: ランタイム・デプロイ先・依存が根本的に異なる。ルートの `pyproject.toml`（本番アプリ）にテスト基盤の依存を混ぜない
- **Trade-offs**: uv プロジェクトが 2 つになり `uv sync` が個別に必要。README で手順を明示して吸収する
- **Follow-up**: ルートの lint/型検査設定が `broker/` をどう扱うかは実装タスクで確認する

### Decision: v0 は GCP 認証情報を一切ロードしない

- **Context**: brief は「Broker のみが GCP 認証情報を使う」と述べるが、v0 の責務はフィクスチャ供給のみ
- **Alternatives Considered**:
  1. v1 を見越して ADC 初期化コードを先行実装
  2. v0 では認証情報関連コードを一切持たない
- **Selected Approach**: 2。v0 のプロセスは `FIXTURE_DIR` 以外の外部リソースに触れない
- **Rationale**: 使わない認証情報をロードするコードは漏洩面を無意味に広げる。時期尚早な実装をしない方針（CLAUDE.md）にも一致
- **Trade-offs**: v1 で実 API 仲介を足す際に認証初期化を新規追加する必要があるが、それは消費者駆動（cloud-runtime-deploy の要求）で行うのが本来の順序
- **Follow-up**: v1 追加時に「認証情報をレスポンス・ログに含めない」検証を再実施する

### Decision: 応答 JSON は `DocumentExtraction` を鏡写しにし、変換ヘルパはテストローカルに置く

- **Context**: フィクスチャ応答はポート契約に「変換可能」であることが求められるが、変換責務は cloud-runtime-deploy のアダプタが所有する
- **Alternatives Considered**:
  1. `src/scanner_rename/` に Broker 応答 → DTO の共有変換モジュールを追加
  2. 変換は `tests/cloud/` 内のテストローカルヘルパに留める
- **Selected Approach**: 2。`cloud` テストが応答 JSON から `OcrResult` / `DocumentExtraction` を実際に構築し、`__post_init__` の不変条件検証を通す
- **Rationale**: 1 は下流スペックのアダプタ責務の先取りになり、境界を侵す。テストローカルなら「変換可能性の証明」だけを所有できる
- **Trade-offs**: cloud-runtime-deploy が後で同種の変換を書く際に重複が生じうるが、契約適合の検証コードとして意図的に独立させる
- **Follow-up**: cloud-runtime-deploy の実装時に、この検証ヘルパを参照実装として案内する

### Decision: 許可リスト = FIXTURE_DIR 直下のケースディレクトリ + 厳格な case_id パターン

- **Context**: `docs/security-notes.md` は case_id → 許可リスト化されたフィクスチャのマッピングを要求する
- **Alternatives Considered**:
  1. マニフェストファイル（allowlist.json）で明示列挙
  2. `FIXTURE_DIR` 直下のディレクトリ集合を許可リストとみなし、case*id を `^[a-z0-9*]+$` に制限
- **Selected Approach**: 2
- **Rationale**: 運用者がフィクスチャを置く行為そのものが許可行為になる（二重管理がない）。パターン制限によりパストラバーサル・隠しファイル参照は構造的に不可能。v0 の規模（5〜6 ファイル）に対しマニフェストは過剰
- **Trade-offs**: 「置いたら公開される」ため、FIXTURE_DIR に無関係なディレクトリを置かない運用前提が生じる。README に明記する
- **Follow-up**: v1 で実 API 仲介（Drive 書き込み等）を足す場合は、操作単位の許可リスト再設計が必要

## Risks & Mitigations

- Broker 未起動のままの cloud テスト実行で原因不明の失敗に見える — 接続失敗を検出して「Broker 未起動/未到達」を明示するメッセージで失敗させる（conftest で到達性を先に検査）
- サンプルフィクスチャと抽出スキーマの乖離（上流スキーマ変更時） — Broker 側単体テストでサンプル全ケースのスキーマ制約（信頼度範囲・期間必須項目・OCR とエビデンスの整合）を検証し、乖離を早期検出する。extraction-pipeline の Revalidation Triggers（スキーマ変更時の 3 スペック横断レビュー）にも依存
- `host.docker.internal` の解決がホスト環境に依存する — 接続先は `GCP_TEST_BROKER_URL` で上書き可能にし、既定値への依存を薄くする
- Broker が誤って LAN に露出する — バインド先は既定 127.0.0.1 とし、README で 0.0.0.0 を使わないよう明記する

## References

- `docs/security-notes.md` — 隔離モデル・Broker 設計制約・フィクスチャポリシー（本スペックのハード制約）
- `broker/README.md` — 想定トポロジー・候補エンドポイント・起動コマンド概念例
- `.kiro/specs/extraction-pipeline/design.md` — `OcrResult` / `DocumentExtraction` / `PortError` 契約（上流所有）
- `docs/adr-candidates/` の ADR 0004 — Broker 経由クラウドアクセスの決定
- [FastAPI](https://fastapi.tiangolo.com/) / [uvicorn](https://www.uvicorn.org/) — 採用スタックの公式ドキュメント
