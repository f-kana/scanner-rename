## ブランチ命名規則

- パターン: `feat/{PBI-ID}-{短い説明}`
- PBI ID は `docs/product-backlog.md` から取得する
- 短い説明は PBI の説明文から英語・kebab-case で自動生成する
- 例: `feat/ph0-005-git-branch-workflow`, `feat/ph2-001-filename-parser`

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
