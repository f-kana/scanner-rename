# PBI-ph0-021: ph0-012 レビュー指摘の軽微即修正バッチ

完了日: 2026年（commit d6bc9d2）

## なぜやったか

ph0-012（Harness 初期版の総合レビュー）で Fable が挙げた軽微な指摘を
一括処理した。互いに独立した修正を 1 ブランチにまとめることで、
個別ブランチの乱立を避けた。

## 修正項目と各 WHY

1. **CLAUDE.md「開発ワークフロー全体」節の書き直し**
   旧手順は `tracking-pbi` 等を直接呼ぶ記述で、スキル側の「必ず
   `my-development-workflow` を経由」という指示と矛盾していた。

2. **`--no-verify` の deny 追加**
   `Bash(git commit *)` が allow のままでは gitleaks を素通りできてしまう。
   secret scanning 導入（ph0-009）の実効性を保つために塞いだ。

3. **`clean-branches/SKILL.md` の `${CLAUDE_PLUGIN_ROOT}` 参照修正**
   外部 APM 由来スキルに未定義変数が残っていた。skill-context-injector での
   補正が効かないケースのため直接修正した。

4. **`classifying-harness/SKILL.md` と `docs/adr-candidates/0008` のパス誤記修正**
   実パス（`.claude/hooks/skill-context-injector/skill-context-injector.sh`）への
   修正。誤記があると skill-context-injector が機能しない。

5. **`skill-context-injector.sh` への `set -euo pipefail` 追加**
   他の hook との一貫性のため。未設定だと silent failure になるリスクがある。

6. **`docs/adr-candidates/0007`（byobu）のステータスを「Accepted」に更新**
   実装済みにもかかわらず「候補」のままになっていた。

7. **`my-development-workflow/SKILL.md` の description 修正**
   「フローを選択・宣言し、そのまま実行する」は誤りで、正しくは
   「宣言し、ユーザーの承認を待ってから実行」。ユーザーが裁定済みの内容。

## 残った制約・注意点

- 外部 APM 由来スキルの直接編集は APM のアップデートで上書きされる可能性がある。
  再導入時に同様の修正が必要か確認すること。
