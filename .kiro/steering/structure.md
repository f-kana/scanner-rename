# Project Structure

## Organization Philosophy

ドメインロジックとインフラアダプターを分離する（ポート/アダプタ）。外部サービス依存のない純粋 Python ロジックをコアに置く。

## Directory Patterns

### docs/

事前インプット素材とプロジェクト運用ドキュメントが混在する。

- `initial-context.md`, `security-notes.md`, `adr-candidates/`: cc-sdd への事前インプット。cc-sdd が正規の仕様を生成した後は歴史的コンテキストとして扱う。
- `product-backlog.md`: PBI 管理で継続的に更新されるアクティブなドキュメント。
- `glossary.md`: 用語定義。継続参照される。

### .kiro/

cc-sdd の仕様・設計・タスク成果物とステアリング。

### app_llm_prompts/

実行時 LLM プロンプト素材。詳細は `steering/tech.md` を参照。

### tmp/

一時ファイル・ワークスペース。プロジェクトルートを汚染しない。

## Naming Conventions

- Files: snake_case (Python)
- Modules: snake_case
- Classes: PascalCase

---

_Document patterns, not file trees. New files following patterns shouldn't require updates_
