# 001-worktree-spec-status

## Prompt

PBI ph0-009 はどういう状態？

（前提: `.claude/worktrees/ph0-009` が存在し、その中の `.kiro/specs/secret-scanning/` に requirements.md / design.md / tasks.md がある。ルートの `.kiro/specs/secret-scanning/` は空ディレクトリ）

## Expected behavior

1. worktree `.claude/worktrees/ph0-009` の存在を確認する
2. `{worktree-path}/.kiro/specs/secret-scanning/` を確認し、tasks.md などの成果物を読む
3. spec.json の phase や tasks.md の完了率をもとに「Tasks 承認済み・実装待ち」と回答する

## Failure behavior to avoid

ルートの `.kiro/specs/secret-scanning/` が空であることだけを根拠に「仕様策定は未開始」と回答する。

## Pass criteria

- worktree 内のパス（`.claude/worktrees/ph0-009/.kiro/specs/...`）を根拠として明示する
- 「Tasks 承認済み・実装待ち」または同等の正しいフェーズを返す

## Negative case

worktree も `.kiro/specs/` も存在しない PBI（例: ph0-003）では「未着手」と正しく返す。
