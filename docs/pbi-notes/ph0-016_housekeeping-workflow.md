# PBI-ph0-016: Housekeeping Workflow の導入

完了日: 2026年（PR #12）

## なぜやったか

機能開発とは性質が異なる保守作業（ブランチ掃除、settings 整頓、メモリ整頓）が
断続的に発生していたが、やり方が属人的で一貫性がなかった。
`my-development-workflow` が機能開発を担うのと対称的に、保守を担う専用の
オーケストレーターが必要だと判断した。

## 選んだアプローチとその理由

`my-housekeeping-workflow` スキルをオーケストレーターとして設置し、
個別処理は既存スキル（`clean-branches` 等）に委譲する構成にした。

理由:

- 保守作業は破壊的操作（ブランチ削除・ファイル書き換え）を含むため、
  必ず「点検 → 宣言・承認 → 実行」の 3 ステップを踏む設計にした
- 個別処理を worktree 掃除・settings 整頓・メモリ整頓に分けて段階的に実装できるよう、
  スキル側は委譲のみ持ち実装を持たない設計にした

## ph0-012 レビューでスコープに追加された項目

初期実装後のレビュー（ph0-012）で以下が追加された:

- `ask` リストの整理: `bypassPermissions` モードでは `ask` が機能しないため、
  本当に止めたい操作は `deny` に移すか不要なら削除すべきという指摘
- `.claude/worktrees/` の worktree 残骸掃除の担い手が未定義だった問題
  （`clean-branches` も `finishing-a-development-branch` も対象外で、
  残骸があると `tracking-pbi` の照会が誤答するリスク）
- `settings.local.json` の整理: 重複エントリ・テスト用一時エントリ・
  `//` 始まりパスなど死にエントリの削除

## 残った制約・注意点

- settings.json / settings.local.json の編集は、変更前後の diff を提示してから適用する
  （破壊的操作のため）
- worktree 残骸削除前に必ずマージ検証を行う（squash マージのケースがあるため
  `git merge-base --is-ancestor` だけでは不十分な場合がある）
