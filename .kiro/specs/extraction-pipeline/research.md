# Research & Design Decisions

## Summary

- **Feature**: `extraction-pipeline`
- **Discovery Scope**: New Feature（アプリケーション層の新設。上流 core-naming-engine 設計との統合が焦点）
- **Key Findings**:
  - core-naming-engine の設計が `NamingInput` / `Period` / `FileState` / 例外規約（判定系は `None`・`UNMANAGED`、生成系は `DomainError`）を確定済みであり、本スペックはこの契約に合わせて抽出結果を射影する
  - 抽出スキーマは `app_llm_prompts/extraction_policy.draft.md` の JSON 案が土台になる。フィールドごとの信頼度・エビデンスを持つ形は Gemini 構造化出力（response schema）と自然に対応する
  - エラーハンドリングは 2 層分担が roadmap で確定済み: 状態遷移（`_needs_review_` / `rename_error_`）は本スペック、インフラリトライは cloud-runtime-deploy

## Research Log

### core-naming-engine との契約整合

- **Context**: 本スペックは抽出結果を命名エンジンに渡す唯一の消費者であり、契約不整合が最大のリスク
- **Sources Consulted**: `.kiro/specs/core-naming-engine/design.md`, `requirements.md`
- **Findings**:
  - `NamingInput(title, document_date, date_has_era, period, issuer)` は命名に必要な射影のみ。信頼度・エビデンスは含まれない（抽出スキーマは本スペック所有と明記）
  - `Period` は `PeriodKind`（CALENDAR_YEAR / FISCAL_YEAR / EXPLICIT_RANGE）+ `year` / `start` / `end`（`YearMonth`）
  - `classify_filename` は全入力を 4 値に分類し例外を送出しない。`build_filename` は `NamingInputError` を送出しうる。`resolve_duplicate(candidate, existing_names)` は既存名一覧を引数で受ける純関数
  - `with_state_prefix` / `strip_state_prefix` で状態遷移のファイル名を生成できる（手動リトライのラウンドトリップ保証あり）
- **Implications**: 信頼度による取捨選択（issuer/period の省略、title 不足の needs_review 判定）は `NamingInput` 生成前のマッパーで完結させる。`build_filename` の `NamingInputError` は本来マッパーで防がれるべきであり、発生時は技術エラー扱いにする

### Gemini 構造化出力スキーマの形

- **Context**: brief が「文書日付、元号、タイトル、発行者、文書種別、年分・年度分・明示期間、信頼度、エビデンス抜粋」をスキーマ所有物として指定
- **Sources Consulted**: `app_llm_prompts/extraction_policy.draft.md`, `docs/initial-context.md`「抽出するメタデータ」節
- **Findings**:
  - ドラフト JSON は `year_part`（暦年）と `fiscal_year_part`（年度 + 期間）を別フィールドにしているが、ドメイン側 `Period` は 3 種を単一の判別共用体で表す
  - エビデンスは「短い抜粋、OCR 全文は返さない」が方針。信頼度は 0.0–1.0
  - 日付優先順位（発行日 > 作成日 > 交付日 > …）と「信頼できる日付がなければ LLM 外でスキャンタイムスタンプにフォールバック」はプロンプト/アプリの分担として既定
- **Implications**: スキーマは「フィールド単位の値 + 信頼度 + エビデンス」の frozen dataclass 群とし、期間はドメインの 3 分類に対応する単一の `ExtractedPeriod` に正規化する（ドラフトの 2 フィールド案より契約が単純になり、マッピングが 1:1 になる）。ドラフト → 確定版でこの構造に更新する

### ポートの粒度と依存注入の形

- **Context**: フェイク・Broker フィクスチャ・実アダプタの 3 実装が同じ契約に従う必要がある（3 スペック共有のシーム）
- **Sources Consulted**: roadmap.md Boundary Strategy、gcp-test-broker / cloud-runtime-deploy の brief、`tests/README.md`
- **Findings**:
  - Broker v0 は OCR / 抽出フィクスチャ供給に徹する。Drive フィクスチャは列挙されていない → Drive ポートの契約はフェイクと実アダプタの 2 実装が主
  - 監視フォルダは `/From_BrotherDevice` 直下固定（v1）。フォルダ解決（パス → ID）は実アダプタの関心事
- **Implications**: DrivePort は「監視フォルダにスコープ済み」の狭い契約（list / download / rename）とし、フォルダ指定をメソッド引数に持たせない。プロンプト素材は ExtractionPort の実装（アダプタ）に構築時に注入し、ポートのメソッドシグネチャには載せない（フェイクはプロンプト不要のため）

### Python での型付きポート表現

- **Context**: tech.md は Pyright 必須。ポートを型検査で強制したい
- **Sources Consulted**: Python typing 標準（`typing.Protocol`）、既存 pyproject.toml（Python >= 3.13, pytest マーカー定義済み）
- **Findings**: `typing.Protocol` は構造的部分型でアダプタ側の継承を不要にし、Pyright が実装適合を静的検証できる。`abc.ABC` は名目的継承を強いる
- **Implications**: 3 ポートは `Protocol` で定義。フェイク・実アダプタは継承なしで適合し、テストで `isinstance` に頼らず型検査で契約遵守を担保する

## Architecture Pattern Evaluation

| Option                           | Description                               | Strengths                                                  | Risks / Limitations                       | Notes                                                    |
| -------------------------------- | ----------------------------------------- | ---------------------------------------------------------- | ----------------------------------------- | -------------------------------------------------------- |
| ヘキサゴナル（ポート/アダプタ）  | アプリ層がポートに依存し、アダプタが実装  | 3 実装（fake/broker/real）が同一契約、外部依存ゼロのテスト | ポート契約の変更コストが 3 スペックに波及 | steering・brief で既定。採用                             |
| トランザクションスクリプト直書き | フローを 1 関数に直書きし、SDK を直接呼ぶ | 最短実装                                                   | フェイク差し替え不能、ローカル検証不能    | 制約（デフォルトテスト外部サービス不要）に反する。不採用 |
| メッセージ/イベント駆動          | ファイルごとにイベントを発行して処理      | スケーラビリティ                                           | v1 のポーリング型バッチ（ADR 0002）に過剰 | 不採用                                                   |

## Design Decisions

### Decision: 抽出スキーマは「フィールド値 + 信頼度 + エビデンス」の値オブジェクト群、期間は単一の判別型

- **Context**: ドラフト JSON は year_part / fiscal_year_part を並列フィールドで持つが、ドメイン `Period` は 3 分類の単一型
- **Alternatives Considered**:
  1. ドラフトのまま並列フィールド — マッピング時に排他制御が必要になり、両方埋まった場合の規則が増える
  2. 期間を `ExtractedPeriod`（kind + year + start/end）に正規化 — ドメイン `Period` と 1:1 対応
- **Selected Approach**: 2。`DocumentExtraction` は `document_date` / `title` / `issuer` / `document_type` / `period` / `reason` を持ち、各フィールドは値 + confidence + evidence の frozen dataclass、欠落は `None`
- **Rationale**: マッパーが機械的になり、needs_review 判定の入力が明確になる。確定版プロンプトにもこの構造を反映する
- **Trade-offs**: LLM 出力 JSON との対応付けをプロンプトで明示する必要がある（実アダプタでの response schema 定義は cloud-runtime-deploy の実装事項）
- **Follow-up**: 確定版 extraction_policy.md にスキーマの JSON 表現を記載し、schema.py と齟齬が出ないよう integration_fake のゴールデンケースで固定する

### Decision: 信頼度ゲートはマッパー（NamingInput 生成前）で一元化

- **Context**: 低信頼度分岐の置き場所（ポート内 / パイプライン内 / マッパー内）
- **Alternatives Considered**:
  1. パイプライン本体に if 分岐を散在させる
  2. マッパーが `ReadyToName | NeedsReview` の判別結果を返す
- **Selected Approach**: 2。`to_naming_decision(extraction, scanner, config)` が「命名可能（NamingInput 付き）」または「要確認（理由付き）」を返す純関数
- **Rationale**: 判定が決定的な純関数になり unit テスト可能。パイプラインは遷移の実行（リネーム）に専念する。core-naming-engine の「判定は None/分類、失敗は例外」という規約とも整合（低信頼度は正常系の分岐であり例外にしない）
- **Trade-offs**: マッパーが設定（閾値）に依存する
- **Follow-up**: 閾値のデフォルト値（0.7）は integration_fake のシナリオで妥当性を確認し、必要なら調整

### Decision: 技術エラーの境界は「ファイル単位の try 境界 + PortError 階層」

- **Context**: 1 ファイルの失敗が他を止めない要件と、低信頼度/技術エラーの区別
- **Alternatives Considered**:
  1. ポートごとに Result 型を返す — Python では冗長で、呼び出し側の網羅チェックが弱い
  2. `PortError` 基底例外（DriveError / OcrError / ExtractionError）+ パイプラインのファイル単位 try
- **Selected Approach**: 2。ファイル単位の try で `PortError` / `DomainError` / 予期しない `Exception` を捕捉し `rename_error_` 遷移。エラー遷移のリネーム自体の失敗は記録して継続
- **Rationale**: 例外はポート契約の一部として明文化する。予期しない例外もファイル境界で吸収しないと隔離要件（5.3）を満たせない
- **Trade-offs**: 広い `Exception` 捕捉はバグを隠しうる → 処理結果 summary に例外種別・メッセージ要約を必ず残す
- **Follow-up**: cloud-runtime-deploy の実アダプタは SDK 例外を必ず PortError 派生に変換すること（Revalidation Trigger に記載）

### Decision: フェイクアダプタは `src/scanner_rename/adapters/fake/` に置く（tests 配下にしない）

- **Context**: フェイクの置き場所
- **Alternatives Considered**:
  1. `tests/` 配下のヘルパー — テスト専用が明確
  2. `src/scanner_rename/adapters/fake/` — 出荷パッケージ内
- **Selected Approach**: 2
- **Rationale**: brief がフェイクアダプタを成果物（境界候補）として明記しており、gcp-test-broker のフィクスチャ設計や将来のローカル実行（ドライラン）が参照する契約実装となる。Pyright によるポート適合の静的検証も src 内の方が確実
- **Trade-offs**: 本番イメージに使われないコードが含まれる（許容: 個人プロジェクト規模、依存追加なし）
- **Follow-up**: 実アダプタ追加時（cloud-runtime-deploy）に `adapters/` 直下の命名規則（fake/ と google/ 等）を維持する

### Decision: プロンプト素材はドラフトを確定版へ昇格し、ローダは実行時に毎回読み込む

- **Context**: ADR 0005（自然言語 Markdown 管理）と要件 6.3（コード変更なしで反映）
- **Alternatives Considered**:
  1. プロンプトを Python 文字列定数に埋め込む — 編集にコード変更が必要
  2. `app_llm_prompts/extraction_policy.md` / `naming_policy.md` をファイルとして読み込む
- **Selected Approach**: 2。`extraction_policy.draft.md` / `naming_policy.draft.md` を確定版（`.draft` なし）に改稿・改名し、ローダが存在・非空を検証して読み込む（欠落は明示的エラー）
- **Rationale**: ADR 0005 の初期構想どおり。Cloud Run へのデプロイ時はイメージに同梱される（パッケージングは cloud-runtime-deploy）
- **Trade-offs**: プロンプトとスキーマ（コード）の二重管理 → integration_fake のゴールデンケースと確定版内のスキーマ記述で整合を担保
- **Follow-up**: README（app_llm_prompts/）の「初期ファイル」記述の更新

## Risks & Mitigations

- ポート契約の変更が gcp-test-broker / cloud-runtime-deploy に波及 — 契約を最小（3 ポート・計 5 メソッド）に保ち、変更時は Revalidation Triggers に従い 3 スペック横断で確認
- LLM 出力のばらつきでスキーマ変換が壊れる — スキーマ型の不変条件（信頼度 0–1、期間種別ごとの必須フィールド）を `__post_init__` で検証し、違反は ExtractionError として技術エラー系へ
- 広い例外捕捉によるバグの潜伏 — 処理結果 summary に例外情報の要約を必須で含め、integration_fake で失敗シナリオを固定
- 同一バッチ内の重複命名 — 実行中に確定した名前を既存名集合へ逐次追加してから `resolve_duplicate` を呼ぶ（設計で明文化、テストで固定）

## References

- `.kiro/specs/core-naming-engine/design.md` — 上流ドメイン契約（NamingInput / FileState / 例外規約）
- `.kiro/steering/roadmap.md` — 2 層エラーハンドリング分担、共有シーム
- `docs/adr-candidates/0005-runtime-llm-prompts-as-md.md` — プロンプト管理方式とコード/プロンプトの責務境界
- `docs/initial-context.md` — 抽出メタデータ一覧、状態管理・手動リトライの合意
- `tests/README.md` — テストカテゴリとフェイクアダプタの初期方針
