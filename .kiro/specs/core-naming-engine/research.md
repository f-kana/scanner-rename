# Research & Design Decisions: core-naming-engine

## Summary

- **Feature**: `core-naming-engine`
- **Discovery Scope**: New Feature（グリーンフィールドだが外部依存ゼロの純ドメインのため、調査は軽量で足りる）
- **Key Findings**:
  - 命名合意は `docs/initial-context.md` と `app_llm_prompts/naming_policy.draft.md` に十分具体的な例付きで存在し、要件へ直接コード化できる
  - 元号変換は必要範囲が狭く（近代 5 元号、ファイル名用略号表記のみ）、外部ライブラリ不要
  - 抽出スキーマは extraction-pipeline 所有のため、本スペックは命名に必要な射影（`NamingInput`）だけを契約として公開すれば境界が濁らない

## Research Log

### 命名フォーマットの合意事項の確定

- **Context**: 要件・設計の唯一の正となるフォーマット定義を確定する
- **Sources Consulted**: `docs/initial-context.md`（基本フォーマット、年分・年度分の例、重複サフィックス例）、`app_llm_prompts/naming_policy.draft.md`（日付フォールバック、タイトル方針、発行元方針）
- **Findings**:
  - 基本形: `<文書日付>_<年分・年度分・期間補足>_<書類タイトル>[_発行元].pdf`
  - 年分: `2025年分`、年度分: `2025年度分(202504-202603)`、元号併記: `20211001(R3)`
  - `対象` の語は使用禁止。文書日付欠落時はスキャンタイムスタンプへフォールバック
  - 発行元・期間の「含めるべきか」の判断は自然言語プロンプト（LLM 側）で管理する方針（ADR 0005）
- **Implications**: 命名エンジンは省略判断を持たず、入力の有無に従う機械的組み立てに徹する。合意例 3 件をゴールデンテストとして完全一致で再現する

### 元号変換の実装方式

- **Context**: 西暦⇔元号変換をどう実装するか（外部ライブラリ vs 自前テーブル）
- **Sources Consulted**: 元号の改元日の公知情報（明治 1868-10-23 / 大正 1912-07-30 / 昭和 1926-12-25 / 平成 1989-01-08 / 令和 2019-05-01）
- **Findings**:
  - 必要なのは「日付→元号+元号年」「元号+年月日→日付」「`(R3)` 形式の略号整形」のみ
  - `japanera` 等のライブラリは旧暦対応など過剰機能であり、依存ゼロ方針（steering: 純粋 Python コア）に反する
  - 明治改元より前（グレゴリオ暦 1868-10-23 より前）は対応表外としてエラーで十分（スキャン対象は現代文書）
- **Implications**: 静的テーブル + 純関数で実装。改元日当日は新元号（公知の運用と一致）。将来の改元はテーブル 1 行追加

### ファイル名サニタイズの基準

- **Context**: Google Drive はほぼ任意の文字を許すが、ローカル同期（Windows/macOS）やユーザーの可読性を考慮した安全側の基準が必要
- **Sources Consulted**: Windows ファイル名禁止文字の一般則（`/ \ : * ? " < > |`、制御文字、末尾ピリオド・空白）
- **Findings**: クロスプラットフォーム安全基準（Windows 準拠）が最も厳しく、これを採用すれば Drive・macOS でも安全
- **Implications**: 禁止文字は `_` に置換し連続 `_` を畳む。上限長は安全マージンを取り 200 文字（Windows の 255 制限とパス長を考慮）

## Architecture Pattern Evaluation

| Option                    | Description                           | Strengths                    | Risks / Limitations              | Notes                       |
| ------------------------- | ------------------------------------- | ---------------------------- | -------------------------------- | --------------------------- |
| 純関数 + frozen dataclass | モジュール = 責務、値オブジェクト中心 | テスト容易、決定的、依存ゼロ | 状態遷移の実行はアプリ層に委ねる | 採用。steering の方針と一致 |
| ドメインサービスクラス群  | NamingService 等のクラスで構成        | DI しやすい                  | 状態を持たないのにクラスは過剰   | 不採用（セレモニー過多）    |
| ルールを YAML 外部化      | 命名規則を設定ファイルで表現          | 非エンジニアが編集可能       | ADR 0005 で明示的に不採用済み    | 不採用                      |

## Design Decisions

### Decision: `NamingInput` を本スペックが所有する契約とする

- **Context**: 抽出メタデータのスキーマは extraction-pipeline が所有するが、命名エンジンには入力型が必要
- **Alternatives Considered**:
  1. extraction-pipeline の抽出スキーマを本スペックが import する — 依存方向が逆転する
  2. 命名に必要な射影 `NamingInput` を本スペックが定義し、マッピングは上位が行う
- **Selected Approach**: 案 2。`NamingInput`（title / document_date / date_has_era / period / issuer）を公開契約とする
- **Rationale**: ドメイン層が最下層である依存方向を守り、抽出スキーマの変更（信頼度・エビデンス等）から命名ロジックを隔離する
- **Trade-offs**: extraction-pipeline にマッピング層が 1 枚増えるが、契約が明示化されレビューしやすい
- **Follow-up**: extraction-pipeline のスペック作成時に `NamingInput` へのマッピングを設計に含めること

### Decision: パース失敗は `None`、生成失敗は例外

- **Context**: 「スキャナー生成名でない」と「命名できない」の性質が異なる
- **Alternatives Considered**:
  1. すべて例外
  2. すべて Result 型（自作）
  3. 判定系は `None`/enum、生成系は例外
- **Selected Approach**: 案 3
- **Rationale**: 判定系はあらゆる入力が正常系（Drive には任意の名前のファイルが置かれ得る）。生成系の失敗は上位の状態遷移（rename_error 等）を要求する真の失敗。Result 型自作は Python では過剰
- **Trade-offs**: 呼び出し側が 2 つの失敗様式を扱うが、それぞれの意味が型に現れる

### Decision: 重複解決は既存名一覧を引数に取る純関数

- **Context**: 重複判定には Drive のフォルダ内容が必要だが、本スペックは I/O 禁止
- **Selected Approach**: `resolve_duplicate(candidate, existing_names)` として、一覧取得は呼び出し側の責務にする
- **Rationale**: I/O ゼロ制約の維持。TOCTOU（取得と適用の間の競合）はアプリ層・実アダプタ側の関心事として明確に外に置く
- **Trade-offs**: 完全な重複回避は保証できない（Drive 側の同時書き込み）が、v1 は単一ジョブ・単一ユーザーのため実害なし
- **Follow-up**: extraction-pipeline で一覧取得→重複解決→リネームの順序を設計すること

### Decision: 元号元年は `R1` と表記する

- **Context**: 合意例（`R3`, `R8`）に元年のケースが現れない
- **Selected Approach**: 略号 + アラビア数字で統一し、元年も `R1` とする（`R元` としない）
- **Rationale**: ファイル名のソート性・機械可読性を優先。合意例の表記体系（略号+数字）と一貫する
- **Follow-up**: ユーザーが `元` 表記を望む場合はテーブル整形部のみの変更で済む

## Risks & Mitigations

- 命名フォーマットの将来変更で既存リネーム済みファイルと不整合 — フォーマット組み立てを naming モジュールに集約し、変更時の影響を 1 箇所に限定。Revalidation Triggers に明記
- 元号テーブルの将来の改元 — テーブル 1 行追加で対応可能な構造にし、境界テストをパラメタライズで整備
- サニタイズが厳しすぎて日本語タイトルを壊す — 置換対象を ASCII 禁止文字と制御文字に限定し、日本語（全角文字）は無加工で通す

## References

- `docs/initial-context.md` — 命名フォーマット・状態管理・手動リトライの一次合意
- `app_llm_prompts/naming_policy.draft.md` — 日付フォールバック・タイトル・発行元の方針（LLM 側ポリシー）
- `docs/adr-candidates/` — ADR 0003（ステートストアなし）、ADR 0005（命名ポリシーは自然言語プロンプト管理）
- `.kiro/steering/structure.md` — 純粋 Python コア方針
