# プロダクトバックログ

このドキュメントは cc-sdd 実行前の大きな作業フェーズと PBI を記録します。

cc-sdd が正規の `requirements.md`、`design.md`、`tasks.md` を生成した後は、それらが正となります。このドキュメントは歴史的コンテキストとして扱ってください。

## Phase 0: プロジェクト骨格

### 基礎 （Python、VS Code等）

- [x] PBI-ph0-001: `pyproject.toml`、uv、pytest、ruff 等
- [x] PBI-ph0-001-1: カバレッジ計測機能の追加
- [x] PBI-ph0-001-2: VS Code 設定整備(.vscode/settings.json)
- [x] PBI-ph0-001-3: VS Code Extensionの整備(.vscode/extensions.json) + pyright導入
- [x] PBI-ph0-001-4: Prettier 導入（package.json、.prettierrc、Node.js 依存）
- [x] PBI-ph0-001-5: Python コーディング規約の導入
- [x] PBI-ph0-002: DevContainer 設定（`.devcontainer/`）(初期設定まで)
- [x] PBI-ph0-002-1: DevContainerの起動、基本動作の動作確認
- [x] PBI-ph0-002-2: DevContainer内でのGitHub認証設定（Push/Pull）
- [ ] PBI-ph0-003: CI の最小構成（lint + unit test）
- [x] PBI-ph0-004: Claude Code Hooksの設定
- [x] PBI-ph0-005: PBIに着手したらGitでFeatureブランチを切る+worktreeするところから開始するよう開発WorkflowをUpdateする
- [x] PBI-ph0-006: Ruff Formatterの改善（VS Code Extensionが効いてない？）

### 応用的開発補助ツール

- [x] PBI-ph0-007-1: Terminalマルチプレクサの導入：tmux
- [x] PBI-ph0-007-2: Terminalマルチプレクサの導入：byobu
- [x] PBI-ph0-007-3: Terminalマルチプレクサの導入：zellij
- [x] PBI-ph0-007-4: Terminalマルチプレクサの導入：herdr

### 追加Harness

- [x] PBI-ph0-008: 長いLLM処理が終わった or 人間への承認依頼で長い処理が中断した場合に、効果音が出るようにしたい。なぜなら、タスクの終わり/中断に僕が気づけるからだ。
- [x] PBI-ph0-009: Secret scanning の導入（pre-commit に gitleaks を追加）。認証情報隔離は整備済だが、git commit レベルでの自動検出がない。
- [x] PBI-ph0-010: Conventional Commits の導入（commitlint + commit-msg hook）。コミットメッセージの統一フォーマット化。
- [x] PBI-ph0-011-2: statusLine のカスタマイズ（モデル名、コンテキスト使用量、コスト情報の表示）

### CC-SDD

- [x] PBI-ph0-011: cc-sddの導入、最低限の初期設定。cc-sddの流儀に併せたSKILLファイル等の再配置が必要なら。
- [x] PBI-ph0-011-1: cc-sdd仕様リファレンスの整備（docs/cc-sdd/配下に reference.md, faq.md を配置、CLAUDE.mdから参照）※成果物は未作成のまま完了扱いになっていた。ph0-012 レビューで「kiro-\* スキル本文が手順を内包しており現状不要（YAGNI）」と裁定。必要になったら再起票する。
- [x] PBI-ph0-012: Harness初期版の総合レビュー。（CIは後回しにするのでそれ以外の)不足のレビュー。成果は ph0-020〜022 と ph0-016 スコープ追記に反映。

### Harness改善・追加

- [x] PBI-ph0-013: skill-context-injectorの微修正。
- [x] PBI-ph0-014: DevContaienrへのghコマンドの導入。
- [x] PBI-ph0-015: AI Agent活動補助としてAST解析(かLS？P)の何かを入れる。ほんとうに必要かはしらんが、試しに使ってみる。-> 既にpyrightが使えたのでこのPBIは保留。
- [x] PBI-ph0-016: 通常の開発Workflowとは異なるWorkflowを導入する（想定はhousekeeping。.claude/settings[.local].jsonやmemoryの整頓などをやる最上位のWorkflow。
- [x] PBI-ph0-016-1: Git branchのお掃除をやるSKILLまたはSubAgentの追加
- [x] PBI-ph0-018: curating-harness SKILLの新規作成とclassifying-harnessとの連携追加。ハーネス構成要素の外部調達・自作判断プロセスを定義。
- [x] PBI-ph0-019: VS Code Built-in ブラウザ向け Host OS パス解決 Harness。HTML の目視確認時に DevContainer パスではなく Host OS パスを提示できるようにする。
- [x] PBI-ph0-020: セキュリティ隔離モデルのドキュメント修正。security-notes.md / initial-context.md の「認証情報はホストのみ」記述を実態（named volume で ADC がコンテナ内に存在）に合わせて書き直す。ph1-001 のブロッカー。
- [x] PBI-ph0-021: ph0-012 レビュー指摘の軽微即修正バッチ（CLAUDE.md ワークフロー節の更新、--no-verify の deny 追加、パス誤記修正ほか）。
- [x] PBI-ph0-022: Herdr SKILLの導入(APM) `https://github.com/ogulcancelik/herdr/blob/master/SKILL.md`
- [x] PBI-ph0-023: `my-development-workflow` の軽量フローに Worktree オプションを追加。重量作業と並行して軽量作業を行う場合でも、ブランチ競合を避けるために Worktree を使えるようにする。
- [x] PBI-ph0-024: apm-usage SKILLの追加
- [x] PBI-ph0-025: curating-harness の APM 利用可否判定ロジック追加。外部スキル導入時に「対象 repo に apm.yml がない」だけで APM を除外する誤判断を防ぐ。path: 仮想パッケージ形式の活用基準も明記する。
- [x] PBI-ph0-026: 完了済みPBI詳細の移動・記録 Harness 整備。`product-backlog.md` の PBI詳細セクションから完了済みPBI詳細を `docs/pbi-notes/` に移動する仕組みを追加。`my-development-workflow` にクローズアウトノート作成ステップ、`my-housekeeping-workflow` に移動漏れ検出ステップ、`tracking-pbi` に `[x]` マーク時の注意書きを追加する。

## Phase 1: cc-sdd 実行

`docs/` の事前インプットを使って cc-sdd を実行し、正規の仕様・設計・タスクを生成する。

ここから先は cc-sdd の成果物が作業の正となる。

- [x] PBI-ph1-001: cc-sdd の実行。入口は `/kiro-discovery`。Phase 2〜6 の分解とスペック分割（single / multi）の対応を Discovery で突き合わせる。（2026-07-08 完了: 4 スペック分割を `.kiro/steering/roadmap.md` に記録し、`/kiro-spec-batch` で全スペック生成・クロススペックレビュー済み）
- [x] PBI-ph1-002: 生成された `requirements.md`、`design.md`、`tasks.md` のレビュー。Fable セッションで実施する。クロススペックレビューの minor 指摘 4 件を観点に含める。（2026-07-08 完了: 4 件 + 新規 1 件を反映。詳細は `docs/pbi-notes/ph1-002_spec-review.md`）

## Phase 2〜6: プロダクト本開発（cc-sdd スペックに再定義済み）

PBI-ph1-001 の Discovery / `/kiro-spec-batch`（2026-07-08）で、旧想定 PBI（ph2-001〜ph6-003）を以下の 4 スペックに再定義した。旧 PBI 一覧はスペックの tasks.md に吸収されたためここからは削除し、作業の正は `.kiro/specs/{feature}/tasks.md` と `/kiro-spec-status` とする。当時挙げていた不足観点（LLM プロンプト設計、Gemini 構造化出力スキーマ、エラーハンドリング・リトライ戦略、Broker 経由のローカル E2E）は各スペックのスコープに吸収済み。

進め方: 依存順に直列。スペックごとに 1 セッションで `/kiro-impl {feature}` を実行する。実装セッションは Vertex（Opus/Sonnet）、スペックレビュー・`/kiro-validate-impl`・例外時のデバッグ判断は Fable セッションで行う。各 PBI の完了条件は tasks.md 全完了 + `/kiro-validate-impl` 通過。

- [~] PBI-ph2-101: `/kiro-impl core-naming-engine` — 純ドメイン層（旧 ph2-001〜005 を包含）
- [ ] PBI-ph2-102: `/kiro-impl extraction-pipeline` — ポート/フェイク/スキーマ/プロンプト/アプリフロー（旧 ph3-001〜003 を包含）
- [ ] PBI-ph2-103: `/kiro-impl gcp-test-broker` — ホスト側 Broker v0（旧 ph4-001〜002 を包含）
- [ ] PBI-ph2-104: `/kiro-impl cloud-runtime-deploy` — 実アダプタ/クラウド統合テスト/デプロイ/監視（旧 ph5-001〜002、ph6-001〜003 を包含）

再定義前にクローズ済みの旧 PBI（歴史的記録として保持）:

- [x] PBI-ph2-006: cc-sddの上位に置くSKILL: development-workflowの作成。（Phase 0 で `my-development-workflow` として前倒し実装済み。ph0-012 レビューで確認しクローズ）

--

# PBI詳細

詳細を補足する必要のあるPBIについて、個別に記述する。

- 本来のPBI詳細の置き場は `docs/pbi-notes/` であり、以下は軽量な・暫定的なPBI詳細情報置き場。
- cc-sdd を経由しない PBI は完了時に `docs/pbi-notes/` へ移動する。
- cc-sdd を経由する PBI は Spec/Requirement 作成時にここから削除する。
