---
name: retrospecting-harness
description: Analyzes Claude Code sessions with misalignment, repeated corrections, unexpected agent behavior, or hard-won workflow lessons. Use after development sessions to propose safe, reviewable updates to CLAUDE.md, project skills, rules, hooks, slash commands, tests, CI, or eval cases.
---

# Retrospecting Harness

このSkillは、Claude Codeのセッションで開発タスクが完了した後に、当該セッションの会話履歴からユーザーの期待とClaudeの行動がズレた箇所を分析し、同様の紆余曲折の再発を減らす（ユーザーの意図に沿った生成を一発で行う）ためのharness改修案を作る。

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
* 環境設定（sandbox、permissions、hooks、settings）の不備による摩擦

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
* 環境設定の不備（sandbox許可、permissions、hooks設定がツールチェインと合っていない）
* 今回だけの文脈依存

### 3. 対象スキルの外部/自作判定と、カスタマイズ機構の確認

反映先を選ぶ前に、プロジェクトに既存のカスタマイズ機構がないか確認する。

確認対象：
- `.claude/hooks/skill-context-injector/skill-context-injector.sh` とその対象ディレクトリ（`.claude/hooks/skill-context-injector/context/`）
  - APM で導入した外部スキルの挙動を SKILL.md を変更せずにカスタマイズできる
- `.claude/settings.json` の hooks 設定
- 既存の path-scoped rules（`.claude/rules/**`）
- 既存の Skill、SubAgent、slash command

#### 外部導入パーツの判定手順

以下の順で確認：

1. `apm.yml` の dependencies に対象が含まれているか（例: `mizchi/skills/meta/empirical-prompt-tuning`）
2. `apm_modules/` に該当パッケージが存在するか
3. `.devcontainer/post-create-command.sh` に `apm install`、`npx cc-sdd` 等があるか
4. `.devcontainer/Dockerfile` に外部パッケージインストールがあるか
5. `node_modules/.cache/_npx/` に npx パッケージが存在するか
6. `CLAUDE.md` に外部パッケージの言及があるか（例: `gotalab/cc-sdd`）
7. `.claude/skills/{skill-name}/` に LICENSE、package.json 等があるか

いずれにも該当しない場合は自作スキル。SKILL.md を直接編集してよい。

いずれかで外部導入と判明した場合、以下の対応優先度を適用。

**外部導入パーツの書き換えには慎重になる:**

Plugin、APM、NPX SKILL コマンド等で外部から導入された SKILL やその他のパーツ（SubAgent、hooks、slash commands）は、直接書き換えるとアップデート時に競合や上書きされるリスクがある。

対応優先度:
1. skill-context-injector（`.claude/hooks/skill-context-injector/context/`）でカスタマイズできるか確認
2. path-scoped rules（`.claude/rules/**`）で制約を追加できるか確認
3. 上記で不十分な場合のみ、SKILL.md の直接編集を検討（ただしその場合も、管理方法や競合リスクをユーザーに明示して確認する）

外部 APM パッケージのスキル（grilling、skill-creator、empirical-prompt-tuning など）を変更したい場合は、SKILL.md を直接編集するのではなく、skill-context-injector を優先する。

### 4. 反映先を選ぶ

**前提条件:** 対象スキルに関わる反映先を選ぶ前に、「3. 対象スキルの外部/自作判定」を完了させること。
判定なしに skill-context-injector か SKILL.md 直接編集かを選んではならない。

各学びを、適切な反映先に分類する。

**分類が複雑な場合や、CLAUDE.md への変更が含まれる場合は、`classifying-harness` スキルを明示的に呼び出して判断を委ねる。**

ただし、外部 APM 導入スキルの挙動調整だけで、カスタマイズ方法が明確（skill-context-injector で対応可能）な場合は、このスキル内で完結してよい。

| 反映先                | 使う条件                              |
| ------------------ | --------------------------------- |
| skill-context-injector | APM外部スキルの挙動をカスタマイズする（SKILL.mdを変更せずに済む） |
| `CLAUDE.md`        | project全体で常に有効な前提・制約・重要コマンド（最後の手段） |
| `SKILL.md`         | 特定ワークフローの手順・判断基準・進め方              |
| `.claude/rules/**` | ファイル種別、ディレクトリ、技術スタック、特定パスに閉じた規約   |
| hooks              | コマンドや静的解析で機械的に検出・強制できるもの          |
| slash command      | 何度も使う定型プロンプト                      |
| tests / CI         | 期待動作をコードやパイプラインで検証できるもの           |
| eval cases         | Skillやharness改善の再発テスト             |
| メモリ               | 個人属性（スキルレベル、言語の得意不得意）やプロジェクト文脈の記録 |
| 反映しない              | 今回限り、事実不明、一般化すると害が大きい、既存指示と矛盾するもの |

CLAUDE.mdへの変更を提案する場合は、`classifying-harness`スキルのCLAUDE.md change reviewチェックリストを実行する。

### 5. 提案を作る

**前提条件:** スキルの変更を含む提案を書く前に、必ず「3. 対象スキルの外部/自作判定」を完了させること。
判定を済ませていない状態で「context injector 経由」「SKILL.md 直接編集」などの反映先を proposal に書いてはならない。
自作スキルに context injector を提案する、外部スキルを直接編集する、といった誤分類が起きるのは判定を省略したときである。

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

### 6. 承認後に適用する

ユーザーが承認したproposalだけを適用する。

適用時のルール:

* 既存ファイルを先に読む
* 既存指示との重複・矛盾を確認する
* 最小差分にする
* 強すぎる`MUST`を乱用しない
* 変更理由が分かる表現にする
* 可能ならeval/testも追加する
* 広範囲・破壊的・不確実な変更は保留して確認する

### 7. Skill変更時はeval化する

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

CLAUDE.md変更を提案する場合は、`classifying-harness`スキルのCLAUDE.md change reviewチェックリストに従うこと。

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
