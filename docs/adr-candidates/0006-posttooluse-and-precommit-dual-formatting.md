# ADR-0006: PostToolUse と Pre-commit の両立

## Status

Accepted (with known trade-off)

## Context

コードフォーマットを2つの段階で実行する：

1. **PostToolUse hook** (`.claude/hooks/post-edit-format.sh`)
   - Claude Code の Edit/Write ツール実行直後に発火
   - `uv run pre-commit run --files "$FILE"` を呼び出し
   - Claude が次に読むコードは常にフォーマット済み

2. **Pre-commit hook** (`.pre-commit-config.yaml`)
   - `git commit` 時に発火
   - ruff (linter + formatter) と prettier を実行
   - コミット前の最終チェック、人間の編集もカバー

## Decision

当面は両方を維持する。

### 理由

- **PostToolUse の価値**: Claude への即座のフィードバック、常にクリーンなコードを提供
- **Pre-commit の価値**: 業界標準、git history の品質保証、人間の編集にも適用
- **設定の一元化**: PostToolUse は pre-commit を呼ぶだけなので、設定は `.pre-commit-config.yaml` に集約

### 実装の工夫

- PostToolUse から pre-commit を呼び出すことで、フォーマッタのバージョンや引数のダブルメンテを回避
- Pre-commit のキャッシュにより、2回目以降は高速（100-150ms）

## Consequences

### Positive

- Claude が生成・編集したコードは常にフォーマット済み
- Pre-commit により git history の品質も保証
- 設定が `.pre-commit-config.yaml` に一元化

### Negative

- **重複フォーマット**: Claude が編集したファイルは PostToolUse と Pre-commit で2回フォーマットされる
- **オーバーヘッド**: 1編集あたり ~100-150ms、10編集で累積 1-1.5秒

### Known Risk

編集頻度が非常に高いセッションでは体感で遅くなる可能性がある。

- **顕在化条件**: 1セッションで50+回の編集、累積 5-7.5秒のオーバーヘッド
- **対処方法**: PostToolUse hook を削除し、pre-commit のみに統一
- **判断基準**: 開発中に「フォーマット待ちが気になる」と感じたら再検討

## Notes

- 2026-06-24 時点では、編集頻度は低く、オーバーヘッドは体感レベルに達していない
- Code review で指摘された #4 (Duplicate formatting work) への対応として記録
