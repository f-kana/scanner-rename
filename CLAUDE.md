# CLAUDE.md

## 重要な指示

- 日本語を使う
- 問題の解消や実装方針立案時に、場当たり的な対応の採用はしてはならない。既存の実装や世の中のベストプラクティスを調査して、最も洗練された手法を採用すること。

### 開発ワークフロー全体

機能開発開始時の手順:

1. ユーザーから開発対象のPBIの指示をもらい、`tracking-pbi` で PBI を進行中に更新
2. `using-git-worktrees` で worktree を作成（命名規則は context injector が注入）
3. cc-sdd のフロー（仕様策定 → 実装）に入る

機能開発完了時の手順:

1. `finishing-a-development-branch` で PR 作成またはマージ
2. `tracking-pbi` で PBI を完了に更新
3. `retrospecting-harness`でHarnessに関する振り返りと改善

## Agentic SDLC and Spec-Driven Development (cc-sdd)

このプロジェクトは [gotalab/cc-sdd](https://github.com/gotalab/cc-sdd) v3 による Kiro-style Spec-Driven Development を中心に開発する。「cc-sdd」には Spex 系と呼ばれる別系統も存在するが、本プロジェクトでは Kiro 系（`.kiro/` ディレクトリ、`/kiro-*` スキル）のみを使用する。ウェブ検索時に Spex 系の情報を混同しないこと。

### Project Context

#### Paths

- Steering: `.kiro/steering/`
- Specs: `.kiro/specs/`

#### Steering vs Specification

Steering (`.kiro/steering/`) - プロジェクト全体のルールとコンテキストで AI をガイドする
Specs (`.kiro/specs/`) - 個別機能の開発プロセスを形式化する

#### Active Specifications

- `.kiro/specs/` でアクティブな仕様を確認
- `/kiro-spec-status [feature-name]` で進捗確認

### Minimal Workflow

- Phase 0 (optional): `/kiro-steering`, `/kiro-steering-custom`
- Discovery: `/kiro-discovery "idea"` — アクションパスを決定、マルチスペックプロジェクトでは brief.md + roadmap.md を生成
- Phase 1 (Specification):
  - Single spec: `/kiro-spec-quick {feature} [--auto]` or step by step:
    - `/kiro-spec-init "description"`
    - `/kiro-spec-requirements {feature}`
    - `/kiro-validate-gap {feature}` (optional: 既存コードベース向け)
    - `/kiro-spec-design {feature} [-y]`
    - `/kiro-validate-design {feature}` (optional: 設計レビュー)
    - `/kiro-spec-tasks {feature} [-y]`
  - Multi-spec: `/kiro-spec-batch` — roadmap.md から依存ウェーブ順に全スペックを並列作成
- Phase 2 (Implementation): `/kiro-impl {feature} [tasks]`
  - タスク番号なし: autonomous モード（タスクごとのサブエージェント + 独立レビュー + 最終検証）
  - タスク番号あり: manual モード（選択タスクをメインコンテキストで実行、レビューゲートあり）
  - `/kiro-validate-impl {feature}` (スタンドアロン再検証)
- Progress check: `/kiro-spec-status {feature}` (いつでも使用可)

### Skills Structure

Skills are located in `.claude/skills/kiro-*/SKILL.md`

- Each skill is a directory with a `SKILL.md` file
- Skills run inline with access to conversation context
- Skills may delegate parallel research to subagents for efficiency
- Additional files (templates, examples) can be added to skill directories
- `kiro-review` — task-local adversarial review protocol used by reviewer subagents
- `kiro-debug` — root-cause-first debug protocol used by debugger subagents
- `kiro-verify-completion` — fresh-evidence gate before success or completion claims
- スキルが現在のタスクに該当する可能性が 1% でもあれば、スキルを呼び出すこと。タスクが単純に見えてもスキルを省略しない。

### Development Rules

- 3フェーズ承認ワークフロー: Requirements → Design → Tasks → Implementation
- 各フェーズでヒューマンレビューが必要。意図的なファストトラック時のみ `-y` を使用
- Steering を最新に保ち、`/kiro-spec-status` で整合性を確認
- ユーザーの指示に正確に従い、そのスコープ内で自律的に行動する: 必要なコンテキストを収集し、要求された作業をエンドツーエンドで完了する。質問は不可欠な情報が欠けている場合か、指示が重大に曖昧な場合のみ行う。

### Steering Configuration

- `.kiro/steering/` 全体をプロジェクトメモリとしてロード
- デフォルトファイル: `product.md`, `tech.md`, `structure.md`
- カスタムファイルもサポート（`/kiro-steering-custom` で管理）

### 成果物の優先順位

cc-sdd フローが生成するまで、最終的な `requirements.md`、`design.md`、`tasks.md` を手動で作成したり、過度に詳細化したりしないでください。

以下のドキュメントは cc-sdd への事前インプット素材としてのみ使用します：

- `docs/initial-context.md`
- `docs/security-notes.md`
- `docs/adr-candidates/*.md`
- `docs/product-backlog.md`

cc-sdd が正規の仕様/設計/タスクを生成した後は、生成された cc-sdd 成果物を正とします。矛盾が生じた場合は、コアな挙動を変更する前にユーザーに確認してください。

## シークレットと認証情報

認証情報やトークンを読み取り、印刷、コピー、または外部に持ち出してはいけません。クラウド統合テストはホスト側 GCP Test Broker 経由のみで実行します。詳細なルールは `.claude/rules/security.md` を参照。

## 開発スタイル

小さくテスト可能なステップを優先します。

認証・接続設定（GitHub、DB、API等）では、新規設定の前に動作確認（dry-run、read-only操作）を行います。既に動作している場合は設定を変更しません。

設定ファイル（`.gitignore`、linter設定、CI設定など）やツールの利用パターンについては、公式テンプレートやドキュメントの推奨方法を先に調査し、それに従います。独自のカスタムパターンを作る前に、標準的なアプローチが存在しないか確認してください。

プロジェクトの設定やルールの変更はこのリポジトリ内で完結させます。`~/.claude/` など、リポジトリ外のユーザースコープ設定を変更しないでください。

一時ファイルやワークスペースは `tmp/` に置く。プロジェクトルートを汚染しない。

## その他の指示

- Prompting に音声入力を使うことがあるため、プロンプトが誤変換を多く含むケースがある。誤変換であることを前提にプロンプトを解釈せよ。

### 時期尚早な実装をしない

cc-sdd が `tasks.md` を生成するまで、明示的に求められない限り以下を実装しないでください：

- 最終的な本番 Cloud Run デプロイメント
- Terraform/IaC
- Drive の完全な E2E
- Firestore またはその他のステートストア
- Slack/Gmail への直接通知
- プロジェクト固有の `.claude/skills/` の新規作成（既存スキルの使用は可）

### ファイル作成時のルール

- 作成予定のファイルは先に`touch`で空ファイルを生成しておく。理由：Write Toolは既存ファイルへの書き込み前にRead Toolの実行を必須とする仕様であり、このReadがpath-scopeルール（`.claude/rules/*.md`）の読み込みをトリガーするため。
- テスト・検証用の一時ファイルは `tmp/` に置く。プロジェクトルートを汚染しない。

### ドキュメント編集のルール

README やドキュメントを編集する前に、`.claude/rules/markdown-style.md` を確認する。特に：

- 設定ファイルと同じディレクトリの README では WHAT（コマンド一覧、環境変数一覧、ツール一覧）を書かない
- WHY（なぜこの構成か、何を試して駄目だったか、どういう制約があるか）を中心に書く
- コマンドの使い方は公式ドキュメント（`man`、`--help`）へのリンクで済ませる
