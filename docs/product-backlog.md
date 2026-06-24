# プロダクトバックログ

このドキュメントは cc-sdd 実行前の大きな作業フェーズと PBI を記録します。

cc-sdd が正規の `spec.md`、`design.md`、`tasks.md` を生成した後は、それらが正となります。このドキュメントは歴史的コンテキストとして扱ってください。

## Phase 0: プロジェクト骨格

Python プロジェクトのセットアップ。

- [x] **PBI-ph0-001** `pyproject.toml`、uv、pytest、ruff 等
- [x] **PBI-ph0-001-1** カバレッジ計測機能の追加
- [x] **PBI-ph0-001-2** VS Code 設定整備(.vscode/settings.json)
- [x] **PBI-ph0-001-3** VS Code Extensionの整備(.vscode/extensions.json) + pyright導入
- [x] **PBI-ph0-001-4** Prettier 導入（package.json、.prettierrc、Node.js 依存）
- [x] **PBI-ph0-001-5** Python コーディング規約の導入
- [x] **PBI-ph0-002** DevContainer 設定（`.devcontainer/`）(初期設定まで)
- [x] **PBI-ph0-002-1** DevContainerの起動、基本動作の動作確認
- [x] **PBI-ph0-002-2** DevContainer内でのGitHub認証設定（Push/Pull）
- [ ] **PBI-ph0-003** CI の最小構成（lint + unit test）
- [x] **PBI-ph0-004** Claude Code Hooksの設定
- [ ] **PBI-ph0-005** PBIに着手したらGitでFeatureブランチを切るところから開始するよう開発WorkflowをUpdateする

## Phase 1: cc-sdd 実行

`docs/` の事前インプットを使って cc-sdd を実行し、正規の仕様・設計・タスクを生成する。

ここから先は cc-sdd の成果物が作業の正となる。

- [ ] **PBI-ph1-001** cc-sdd の実行
- [ ] **PBI-ph1-002** 生成された `spec.md`、`design.md`、`tasks.md` のレビュー

## Phase 2: コアドメインロジック

外部サービス依存なしの純粋 Python ロジック。

- [ ] **PBI-ph2-001** スキャナーファイル名のパースとバリデーション
- [ ] **PBI-ph2-002** 日付処理と元号変換
- [ ] **PBI-ph2-003** 命名エンジン（抽出メタデータからファイル名を生成）
- [ ] **PBI-ph2-004** 重複サフィックスとサニタイズ
- [ ] **PBI-ph2-005** ユニットテスト

## Phase 3: ポート／アダプタとフェイク統合テスト

- [ ] **PBI-ph3-001** Drive、OCR、LLM 抽出のインターフェース定義
- [ ] **PBI-ph3-002** フェイクアダプタの実装
- [ ] **PBI-ph3-003** `integration_fake` テストでアプリケーションフロー全体を検証

## Phase 4: GCP Test Broker v0

Mac ホスト側で動作するテストブローカーの最小実装。

- [ ] **PBI-ph4-001** OCR フィクスチャと抽出フィクスチャ用のエンドポイント
- [ ] **PBI-ph4-002** `broker/` に実装

## Phase 5: 実アダプタとクラウド統合テスト

- [ ] **PBI-ph5-001** Google Drive API、Document AI、Gemini の実アダプタ
- [ ] **PBI-ph5-002** ブローカー経由のクラウド統合テスト

## Phase 6: パッケージングとデプロイと監視

- [ ] **PBI-ph6-001** Cloud Run Job（Dockerfile、エントリポイント）
- [ ] **PBI-ph6-002** 構造化ログと Cloud Monitoring ログベースアラート
- [ ] **PBI-ph6-003** Cloud Scheduler による定期実行
