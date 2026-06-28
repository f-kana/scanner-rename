## ブランチ命名規則

- パターン: `feat/{PBI-ID}-{短い説明}`
- PBI ID は `docs/product-backlog.md` から取得する
- 短い説明は PBI の説明文から英語・kebab-case で自動生成する
- 例: `feat/ph0-005-git-branch-workflow`, `feat/ph2-001-filename-parser`

## EnterWorktree の制約回避

EnterWorktree は以下の変換を強制する（Claude Code の既知の制約）:
- `/` → `+` に置換（例: `feat/ph0-014` → `feat+ph0-014`）
- `worktree-` プレフィックスを追加（例: `feat+ph0-014-...` → `worktree-feat+ph0-014-...`）

参照: GitHub Issues [#28761](https://github.com/anthropics/claude-code/issues/28761), [#31969](https://github.com/anthropics/claude-code/issues/31969), [#62309](https://github.com/anthropics/claude-code/issues/62309)

**回避手順:**
1. EnterWorktree で worktree を作成（どんな名前でも可）
2. worktree 内で正しいブランチ名を作成:
   ```bash
   git checkout -b feat/ph0-XXX-description
   ```
3. 以降の作業は新しいブランチで行う
4. **作業完了時**: EnterWorktree が作った `worktree-*` ブランチを削除:
   ```bash
   git branch -d worktree-<name>
   ```
   
   ただし、以下の場合は削除しなくてよい:
   - worktree がまだ存在する場合（削除できない）
   - ブランチにコミットがない場合（害がない）

詳細は `docs/adr-candidates/0008-git-branch-naming-workaround.md` を参照。

## worktree 作成タイミング

PBI 着手時に worktree を作成する。cc-sdd Phase 1（仕様策定）の前に行うこと。spec ファイルも差分管理の対象にするため。

## セッション再開時の自動検出

セッション開始時に、作業中の PBI に対応する既存ブランチと worktree を検出する:

1. `git worktree list` で `feat/{PBI-ID}-*` パターンの worktree を探す
2. 見つかった場合は `EnterWorktree` の `path` パラメータで再入場する
3. 見つからない場合は新規作成する

基本は 1 PBI = 1 Session を目指す。再入場はフォールバック。

## 言語指定

このスキルの指示は英語で書かれていますが、ユーザーへの応答はすべて日本語で行ってください。技術用語は英語のままで構いません。
