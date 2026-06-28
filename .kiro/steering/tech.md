# Technology Stack

## Architecture

Cloud Run Job ベースのバッチ処理。ドメインロジックをインフラアダプターから分離する（ポート/アダプタ）。

```text
Cloud Scheduler → Cloud Run Job → Google Drive API / Document AI / Gemini → Drive リネーム → Cloud Logging / Cloud Monitoring
```

## Core Technologies

- Language: Python
- Runtime: Cloud Run Job
- OCR: Document AI
- LLM: Gemini（構造化出力）
- Storage: Google Drive API
- Package Manager: uv

## Development Standards

### Testing

pytest マーカーでテストを分類: `unit`, `integration_fake`, `cloud`, `e2e_cloud`。デフォルトのローカルテストは外部サービスを必要としない。詳細は `tests/README.md` を参照。

### Code Quality

- Ruff (linter + formatter)
- Pyright (type checker)
- Prettier (Markdown/JSON formatting)

### Runtime LLM Prompts

`app_llm_prompts/` は、アプリケーションが実行時に Gemini 等の文書解析 LLM に対して使用するプロンプトのためのディレクトリ。Claude Code の指示のためのものではない。

---

_Document standards and patterns, not every dependency_
