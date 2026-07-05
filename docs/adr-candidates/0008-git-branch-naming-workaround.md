# ADR 0008: Git Branch Naming Workaround for EnterWorktree Constraints

## Status

Accepted

## Context

このプロジェクトでは、以下のブランチ命名規則を採用している：

```
feat/{PBI-ID}-{短い説明}
例: feat/ph0-014-gh-cli-setup
```

この規則は以下の理由で選択された：

- Git Flow / GitHub Flow の標準的な慣例に従う
- `/` による階層構造で、ブランチの種類（feature/bugfix/hotfix）を明確にする
- PBI ID でトレーサビリティを確保

しかし、Claude Code の `EnterWorktree` ツールは以下の変換を強制する：

1. `/` を `+` に置換（例: `feat/ph0-014` → `feat+ph0-014`）
2. `worktree-` プレフィックスを追加（例: `feat+ph0-014-gh-cli-setup` → `worktree-feat+ph0-014-gh-cli-setup`）

これは Claude Code の既知の制約であり、コミュニティで複数の Issue が立てられている：

- [Issue #28761](https://github.com/anthropics/claude-code/issues/28761): "Simplify worktree branch naming: use worktree name directly instead of worktree- prefix"
- [Issue #31969](https://github.com/anthropics/claude-code/issues/31969): "Feature: Enter/resume existing worktrees, configurable branch naming, hook removal control"
- [Issue #62309](https://github.com/anthropics/claude-code/issues/62309): "`claude --worktree <name>` bases on origin/<default> not parent HEAD + prepends `worktree-` to branch name"

### 問題

EnterWorktree の制約により、プロジェクトのブランチ命名規則を維持できず、以下の問題が発生する：

1. **チーム標準からの逸脱**: `worktree-feat+ph0-014-gh-cli-setup` は一般的な Git 慣例から外れている
2. **トレーサビリティの低下**: GitHub/GitLab などの UI でブランチを探しにくい
3. **CI/CD との不整合**: ブランチ名パターンマッチングが機能しない可能性
4. **レビュー時の混乱**: PR のブランチ名が予期しない形式

## Decision

EnterWorktree で worktree を作成した後、**手動で正しいブランチ名を作成する**ことで制約を回避する。

### 手順

1. EnterWorktree で worktree を作成（名前は任意）
2. worktree 内で正しいブランチ名を作成:
   ```bash
   git checkout -b feat/ph0-XXX-description
   ```
3. 以降の作業は新しいブランチで行う
4. EnterWorktree が作った `worktree-*` ブランチは**作業完了時に削除**

### 実装

この手順は以下に文書化されている：

- `.claude/hooks/skill-context-injector/context/using-git-worktrees.md`: `using-git-worktrees` スキルへのコンテキスト注入
- `CLAUDE.md`: 開発ワークフロー全体の中で参照

## Consequences

### Positive

- プロジェクトのブランチ命名規則を維持できる
- Git の標準的な慣例に従ったブランチ名を使用できる
- GitHub/GitLab などの UI でブランチを探しやすい
- CI/CD パイプラインとの整合性を保てる

### Negative

- 手動でブランチを作成する手間が増える（1コマンド追加）
- EnterWorktree が作ったブランチを後で削除する必要がある
- Claude が自動化できない手順が含まれる（人間の介入が必要）

### Neutral

- EnterWorktree の制約が解消されれば、この回避策は不要になる
- 上記 GitHub Issues が解決されるまでの暫定対応

## Alternatives Considered

### 1. EnterWorktree の命名をそのまま受け入れる

**却下理由**: プロジェクトのブランチ命名規則を放棄することになり、チーム標準からの逸脱を許容することになる。

### 2. EnterWorktree を使わず、手動で git worktree を作成する

**却下理由**:

- Claude Code の推奨ワークフローから外れる
- EnterWorktree のセッション管理機能（worktree のライフサイクル管理、自動クリーンアップ）を失う
- 手動での worktree 管理はより複雑

### 3. CLAUDE.md でブランチ命名規則を変更する

**却下理由**:

- Git の標準的な慣例から外れることになる
- 他のプロジェクトやチームメンバーとの整合性を失う
- CI/CD パイプラインの変更が必要になる可能性

## Notes

この ADR は、EnterWorktree の制約が解消されるまでの**暫定的な対応**である。

Claude Code の将来のバージョンで以下のいずれかが実現された場合、この回避策は不要になる：

- EnterWorktree に `--branch` パラメータが追加される
- `worktree-` プレフィックスを無効化する設定が追加される
- `/` をそのまま使えるようになる（ディレクトリ名のみサニタイズ）

その場合、この ADR は Superseded 状態に更新し、新しい方法を文書化する。
