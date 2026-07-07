---
name: my-housekeeping-workflow
description: |
  ハーネス自体の保守（掃除・整頓）をオーケストレートする。
  「housekeeping」「掃除」「整頓」「ハーネスの掃除」「settings を整理」
  「worktree を掃除」「メモリを整理」など、開発環境の保守指示で呼び出す。
  機能開発ではなく、ブランチ残骸・worktree 残骸・settings の重複や
  死にエントリ・メモリの陳腐化を診断・掃除する。
---

# Housekeeping Workflow Orchestrator

## 目的

ハーネス（ブランチ、worktree、settings、メモリ）の保守を一貫した手順で行う。
`my-development-workflow` と対をなすオーケストレーターで、機能開発ではなく環境の掃除・整頓を担う。

個別処理の実装は持たない。既存スキル（`clean-branches` 等）への委譲と、スキル未実装領域の手順定義のみを持つ。

---

## 設計上の制約

- 破壊的操作（ブランチ削除・worktree 削除・settings 編集）は Step 2 の承認なしに行わない
- 削除前に必ずマージ検証を行う（Step 3 の worktree 掃除手順を参照）
- settings.json / settings.local.json の編集は、変更前後の diff を提示してから適用する

---

## Step 1: 点検（Inventory）

掃除対象の現状を読み取り専用で診断する。この段階では何も変更しない。

### ブランチ / worktree

1. `git fetch -p` でリモートの最新状態を取得
2. マージ済みローカルブランチの検出
3. `.claude/worktrees/` 以下の worktree 残骸の検出
4. `worktree-*` スタブブランチの検出（EnterWorktree の命名制約回避で残るもの。ADR-0008 参照）

### settings

`.claude/settings.json` と `.claude/settings.local.json` の重複エントリ・死にエントリの検出。

### PBI詳細の移動漏れ

`docs/product-backlog.md` の `# PBI詳細` セクションを読み、
完了済み（`[x]`）PBI の詳細が残っていないか確認する。

- 完了済み PBI の詳細が残っている → 移動漏れとして検出
- 未着手・進行中（`[ ]`/`[~]`）PBI の詳細が残っている → 正常（移動しない）

### メモリ

`MEMORY.md` とメモリファイル群を読み、陳腐化候補を検出する。

---

## Step 2: 宣言と承認

検出結果を「実施する掃除メニュー」としてユーザーに提示する。

```
検出結果:
- ブランチ: マージ済み 3 件、スタブ 2 件
- worktree 残骸: 1 件
- settings: 重複エントリ 2 件
- メモリ: 陳腐化候補 1 件
- PBI詳細の移動漏れ: 2 件（ph0-019, ph0-020）

上記を掃除してよいですか？（個別に除外も可能です）
```

ユーザーの承認を得てから Step 3 に進む。サイレント実行しない。

---

## Step 3: 実行

承認された項目のみ実行する。

### ブランチ掃除

`clean-branches` スキルに委譲する。

### worktree 残骸掃除

以下の手順で実施する:

1. `git worktree list` で `.claude/worktrees/` 以下の worktree を列挙する（現在作業中のものは除外）
2. 各 worktree のブランチについてマージ検証:
   - `git merge-base --is-ancestor <branch> origin/main` で真なら安全
   - 偽なら squash マージの可能性があるため `gh pr list --state merged --search "head:<branch>"` で PR を特定し、`gh pr view <N> --json headRefOid` の SHA とローカルブランチ先端の一致を確認
   - worktree 内に未コミット変更がないことも確認（`git -C <path> status --short`）
3. 検証済みのものだけ `git worktree remove <path>` → `git branch -D <branch>`
4. `worktree-*` スタブブランチは `git rev-list --count origin/main..<branch>` が 0 なら削除
5. リモートのマージ済み feature ブランチ（`origin/feat/*`）の削除は `clean-branches` に委譲

### settings 整頓

変更前後の diff を提示し、ユーザーの確認を得てから適用する。専用スキルが実装されたら差し替える。

### メモリ整頓

陳腐化したメモリファイルの更新・削除を提案する。専用スキルが実装されたら差し替える。

### PBI詳細の移動

移動漏れとして検出した PBI について、`tracking-pbi` スキルを発動して完了後処理を行う。

---

## Step 4: 報告

削除・変更した項目の一覧と、判断を保留した項目を報告する。

```
実施結果:
- 削除: ブランチ 3 件、worktree 1 件、スタブ 2 件
- 変更: settings.json の重複エントリ 2 件を統合
- 保留: メモリ「xxx」は確認が必要なため未処理
```
