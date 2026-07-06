# scanner-rename

Brother スキャナーが Google Drive にアップロードした PDF を、内容に基づいて自動リネームする Cloud Run Job。

スキャナーが生成するファイル名（`20260507132742_001.pdf`）は機械的な連番であり、ファイルを見ただけで内容を判断できない。
手動でリネームすることも選択肢だが、OCR と LLM を組み合わせれば文書内容から適切な名前を生成できる精度が実用レベルに達していると判断し、自動化することにした。

また、cc-sdd を基軸とした Claude Code の Harness 構築実験目的を兼ねる。小規模プロジェクトにしてはやや過剰な Harness が組み込まれることになる。

## 技術スタック

| レイヤー           | 採用技術                             |
| ------------------ | ------------------------------------ |
| スケジューラ       | Cloud Scheduler                      |
| ジョブランタイム   | Cloud Run Job                        |
| ファイルストレージ | Google Drive (`/From_BrotherDevice`) |
| OCR                | Document AI                          |
| 構造化抽出         | Gemini                               |
| 可観測性           | Cloud Logging / Cloud Monitoring     |
| ローカル開発環境   | DevContainer                         |
| 開発エージェント   | Claude Code (cc-sdd)                 |
| 言語               | Python                               |

## セキュリティ上の注意

クラウド統合テストは DevContainer から Google API を直接呼び出さず、ホスト側 GCP Test Broker 経由でのみ実行する。詳細は `docs/security-notes.md` を参照。

## 仕様・設計ドキュメント

正規の仕様・設計・タスクは cc-sdd（Kiro-style Spec-Driven Development）が `.kiro/specs/` に生成する。事前インプット素材は `docs/` に置いており、cc-sdd 生成物と矛盾した場合は生成物を優先する。
