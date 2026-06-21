---
name: harness-retrospective
description: Analyzes Claude Code sessions with misalignment, repeated corrections, unexpected agent behavior, or hard-won workflow lessons. Use after development sessions to propose safe, reviewable updates to CLAUDE.md, project skills, rules, hooks, slash commands, tests, CI, or eval cases.
---

# Harness Retrospective

このSkillは、Claude Codeのセッションで開発タスクが完了した後に、当該セッションの会話履歴からユーザーの期待とClaudeの行動がズレた箇所を分析し、同じ紆余曲折を減らす（ユーザーの意図に沿った生成を一発で行う）ためのharness改修案を作る。

対象harness:

* `CLAUDE.md`
* `.claude/skills/**/SKILL.md`
* `.claude/rules/**`
* `.claude/settings.json`
* hooks
* slash commands
* tests / CI
* eval cases
* agent contextとして使うproject docs

## Primary Rule

最初の応答では、原則としてファイルを変更しない。
まず分析・分類・提案を出し、ユーザーが承認したproposalだけを最小差分で適用する。

ユーザーが「全部適用」「Highだけ適用」「Proposal AとCを適用」などと明示した場合のみ、変更に進む。

## Goal

ユーザーが細かい改善指示を書かなくても、Claude側が再発防止案を作り、人間が主にYes/Noでレビューできる状態を目指す。
ただし、ユーザーの意図の推測が難しい場合は遠慮なく人間に真意を確認すること。ユーザーの意図に沿うHarnessを作ることが一番の目的だからだ。

## When to Use

以下の場合に使う。

* ユーザーが何度も修正指示を出した
* Claudeが作業スコープ、設計方針、実装方針、検証方針を誤った
* 最終的には良い状態に到達したが、不要な往復が多かった
* 既存の`CLAUDE.md`、Skill、rules、hooks、tests、CI、evalに不足や曖昧さがありそう
* 今回の学びを恒久化すべきか判断したい

## Workflow

### 1. セッションから学びを抽出する

会話・作業ログ・差分・ユーザーの修正指示から、以下を抽出する。

* ユーザーの本来の期待
* Claudeのズレた行動
* 追加で必要になった修正指示
* 最終的にうまくいった方針
* 既存harnessに不足していた情報
* 最初から分かっていれば避けられた往復

不明点があっても、すぐ質問しない。
ログから合理的に推定できる範囲で進める。
ただし、誤った恒久化につながる重大な曖昧さがある場合だけ確認する。

### 2. 根本原因を分類する

各問題を、必要に応じて以下に分類する。

* 目的理解不足
* 作業スコープ誤認
* 実装前の計画不足
* 調査不足
* 既存コード理解不足
* テスト・検証不足
* 過剰なリファクタリング
* 変更が小さすぎる
* ユーザー確認タイミングの誤り
* destructive operationの安全確認不足
* project conventionの未把握
* Skillのtrigger不良
* Skill本文の手順不足
* `CLAUDE.md`の情報不足
* rule/hook/test/CI不足
* 既存指示の矛盾
* 今回だけの文脈依存

### 3. 反映先を選ぶ

各学びを、次のいずれかに分類する。

| 反映先                | 使う条件                              |
| ------------------ | --------------------------------- |
| `CLAUDE.md`        | project全体で常に有効な前提・制約・重要コマンド       |
| `SKILL.md`         | 特定ワークフローの手順・判断基準・進め方              |
| `.claude/rules/**` | ファイル種別、ディレクトリ、技術スタック、特定パスに閉じた規約   |
| hooks              | コマンドや静的解析で機械的に検出・強制できるもの          |
| slash command      | 何度も使う定型プロンプト                      |
| tests / CI         | 期待動作をコードやパイプラインで検証できるもの           |
| eval cases         | Skillやharness改善の再発テスト             |
| 反映しない              | 今回限り、事実不明、一般化すると害が大きい、既存指示と矛盾するもの |

### 4. 提案を作る

最初の出力は、最大5個のatomic proposalにする。
High / Medium / Lowを付ける。
High以外は、重要でなければまとめる。

出力形式:

```markdown
## Harness Retrospective Summary

### 今回起きたこと
...

### ユーザーの本来の期待
...

### Claudeのズレ
...

### 根本原因
...

## 改修提案

### Proposal A: <短い名前>
- 推奨度: High / Medium / Low
- 反映先:
- 対象ファイル:
- 問題:
- 変更案:
- 理由:
- 期待効果:
- リスク:
- 過剰一般化リスク:
- 差分案:
- eval/test案:
- 人間の判断ポイント:

## 推奨する適用順
1. ...

## ユーザー確認
以下から選んでください。

- `全部適用`
- `Highのみ適用`
- `Proposal AとCだけ適用`
- `差分だけ見せて`
- `eval caseだけ作って`
- `今回は反映しない`
```

### 5. 承認後に適用する

ユーザーが承認したproposalだけを適用する。

適用時のルール:

* 既存ファイルを先に読む
* 既存指示との重複・矛盾を確認する
* 最小差分にする
* 強すぎる`MUST`を乱用しない
* 変更理由が分かる表現にする
* 可能ならeval/testも追加する
* 広範囲・破壊的・不確実な変更は保留して確認する

### 6. Skill変更時はeval化する

`.claude/skills/**/SKILL.md`を変更する場合は、可能な限り同じ失敗を検出するeval caseを作る。

eval caseには以下を含める。

```markdown
# <case name>

## Prompt
...

## Expected behavior
...

## Failure behavior to avoid
...

## Pass criteria
...

## Negative case
...
```

推奨配置:

```text
.claude/skills/<skill-name>/
  SKILL.md
  evals/
    cases/
      001-<short-name>.md
```

Skill Creatorを使える環境では、このeval caseを使ってold Skill / new Skillを比較できる形にする。

## Decision Rules

### `CLAUDE.md`に入れる

以下をすべて満たす場合のみ。

* project全体で有効
* 頻繁に参照される
* 既存指示と矛盾しない
* 短く書ける
* Skillやruleに閉じ込めるより全体共有が妥当

### Skillに入れる

以下のいずれかを満たす場合。

* 特定作業の手順である
* 実行順序や判断基準が重要
* 何度も繰り返すワークフローである
* `CLAUDE.md`に置くと広すぎる
* trigger descriptionで適用場面を限定できる

### Hook/Test/CIに入れる

以下の場合は自然言語指示より機械的強制を優先する。

* コマンドで検証できる
* 静的解析で検出できる
* フォーマットや生成物整合性の問題
* 失敗時の危険や手戻りが大きい
* 人間が毎回レビューするのが非効率

### 反映しない

以下の場合。

* 今回限りの会話都合
* ユーザーの一時的な例外指示
* 既存harnessに既に書かれている
* ルール化すると過剰制約になる
* 事実関係が不明
* 他の顧客・チーム・プロジェクトに誤適用される可能性が高い

## Quality Bar

提案は以下を満たすこと。

* 人間がYes/Noで判断しやすい
* 変更単位がatomic
* 差分が最小
* 適用範囲が明確
* 再発防止効果が説明されている
* 過剰一般化リスクが明示されている
* 可能ならeval/testで検証できる
* `CLAUDE.md`を不要に肥大化させない
* 自然言語でなく機械的強制すべきものを見逃さない

## Output Style

* 日本語で出力する
* 断定できないことは推測として明記する
* 提案は簡潔にする
* ユーザーに細かいプロンプト作成を要求しない
* 変更前に分類と理由を示す
