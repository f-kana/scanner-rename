# Product Overview

Brother スキャナーのスキャン PDF を自動リネームするシステム。

## Core Capabilities

- スキャンされた PDF を Document AI OCR + Gemini 構造化出力で解析
- 抽出メタデータ（日付、元号、文書種別等）に基づくファイル自動リネーム
- Google Drive 上でのファイル状態管理（成功/低信頼度/エラー）
- 低信頼度・エラー時の通知（Cloud Logging → Cloud Monitoring ログベースアラート → メール）

## Target Use Cases

- 自宅 Brother スキャナーでスキャンした文書の自動整理
- 利用者: 1名（個人プロジェクト）

## Project References

- 詳細コンテキスト: `docs/initial-context.md`
- セキュリティ方針: `docs/security-notes.md`
- アーキテクチャ決定: `docs/adr-candidates/`
- プロダクトバックログ: `docs/product-backlog.md`
- 用語集: `docs/glossary.md`

---

_このプロジェクトは小規模だが、より大きなシステム開発で Claude Code を使う前の練習も兼ねている_
