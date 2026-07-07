---
name: tracking-pbi
description: |
  PBI（プロダクトバックログアイテム）のステータスを管理する。更新と照会の両方を扱う。
  開発作業を伴う PBI 着手（「do PBI-xxx」「PBI-xxx をやる」等）には、
  このスキルではなく my-development-workflow を使うこと。
  以下のような場面で使う:
  - PBI の作業が完了した時 → 完了マーク [x] をつける
  - 「PBI-xxx を完了」「complete PBI-xxx」→ 完了マーク [x]
  - my-development-workflow の内部から呼ばれる（開始・完了マーク）
  - 「PBI-xxx のステータスは？」などの照会 → 複数ソースを確認して回答する
---

# PBI 状態管理

`docs/product-backlog.md` のチェックリストで PBI の状態を管理する。

## 状態遷移

```
[ ]  （未着手）
 ↓  作業開始
[~]  （進行中）
 ↓  作業完了
[x]  （完了）
```

直接 `[ ]` → `[x]` も可（作業が即座に完了した場合）。

## 手順

### 作業開始時

1. `docs/product-backlog.md` を読む
2. 該当 PBI の行を見つける（PBI ID で検索）
3. `- [ ]` を `- [~]` に変更する
4. `docs/pbi-notes/` に該当 PBI ID で始まるファイルがあれば Read してコンテキストに取り込む
5. 通常の作業に進む

### 作業完了時

1. `docs/product-backlog.md` を読む（最新の状態を取得するため）
2. 該当 PBI の行を見つける
3. `- [~]` または `- [ ]` を `- [x]` に変更する
4. クローズアウト処理（pbi-notes 移動など）は `.claude/skills/tracking-pbi/closeout.md` を Read して従う

## PBI 行のフォーマット

```markdown
- [ ] **PBI-ph0-001** 説明テキスト
- [~] **PBI-ph0-002** 説明テキスト
- [x] **PBI-ph0-003** 説明テキスト
```

PBI ID のパターン: `PBI-ph<フェーズ番号>-<連番>` （サブアイテムは末尾に `-<枝番>` がつく場合がある）

## PBI 作業スコープ

PBI タスクでは必要最小限の実装にとどめ、以下のルールを守る。

### 「調査」タスクのスコープ

- 技術的事実の収集と記録のみ行う
- 「導入する/しない」などの意思決定は、明示的な指示がない限り行わない
- 調査結果のドキュメント化（ADR、README等への追加）は、別途指示があるまで行わない

### 複数PBIが並んでいる場合

- product-backlog.md で同じフェーズに複数のPBIが並んでいる場合（例: ph0-007-1, ph0-007-2, ph0-007-3）、その構造から全体意図を推測する
- 例: 「tmux導入」「byobu導入」「zellij導入」が並んでいる → 3つとも試して選択肢を提供する意図と読み取る

### ドキュメント編集

- README.md や既存ドキュメントへの追記は、明示的な指示がある場合のみ行う
- CLAUDE.md の「NEVER create documentation files unless explicitly requested」は README 編集にも適用する
- README を編集する場合は、事前に `.claude/rules/markdown-style.md` を Read して WHAT/WHY ルールを確認する

## ステータス照会手順

PBI のステータスを問われたときは、以下の 3 ソースを確認して総合的に回答する。

1. `docs/product-backlog.md` のチェックマーク
   - `[ ]` 未着手 / `[~]` 進行中 / `[x]` 完了
   - ただし `[~]` への更新が漏れている場合があるため、これだけで未着手と断定しない

2. `.claude/worktrees/` または `.worktrees/` 以下のディレクトリ名
   - PBI ID や feature 名に一致する worktree が存在すれば、進行中の可能性が高い
   - worktree が存在する場合、specs は worktree 内にある可能性が高い（次のステップで worktree 内を優先して確認する）

3. `.kiro/specs/{feature-name}/` の成果物の有無
   - worktree が存在する場合: `{worktree-path}/.kiro/specs/{feature-name}/` を優先して確認する
   - worktree がない場合: ルートの `.kiro/specs/{feature-name}/` を確認する
   - feature-name の特定: `ls .kiro/specs/`（またはworktree内の同パス）で一覧を取得し、PBI の説明文と照合する
   - `requirements.md` あり → Requirements 定義済み
   - `design.md` あり → Design 定義済み
   - `tasks.md` あり → Tasks 定義済み
     - 全タスクが `[x]` → 実装完了
     - 未完了タスクが残る → 実装中または実装前

3 ソースを総合して回答する。例:
> `docs/product-backlog.md` は `[ ]` ですが、`.claude/worktrees/ph0-009/.kiro/specs/secret-scanning/tasks.md` が存在し、
> worktree 上で Tasks 定義済み・実装待ちの状態です。

## 注意

- 編集前に必ずファイルを読み直す（他の変更が入っている可能性がある）
- 該当 PBI が見つからない場合はユーザーに確認する
- 複数の PBI を同時に変更する場合も1つずつ確実に更新する
