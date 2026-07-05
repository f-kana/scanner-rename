---
name: my-development-workflow
description: |
  PBI の開発着手から完了まで、ワークフロー全体をオーケストレートする。
  「do PBI-xxx」「PBI-xxx をやる」「PBI-xxx に着手」など、PBI の作業を
  開始する指示があれば tracking-pbi の代わりにこのスキルを使う。
  「SDDで開発して」「cc-sddで進めて」「仕様策定から始めて」など、
  SDD / cc-sdd フローを指示された場合も kiro-* スキルを直接呼ばず
  このスキルを経由すること。
  タスクの規模を評価してフローを選択・宣言し、ユーザーの承認を待ってから実行する。
  開発作業を伴う PBI 指定や SDD 開始指示が来たら、必ずこのスキルを呼ぶこと。
---

# Development Workflow Orchestrator

## 目的

PBI 着手時に「どのフローで進めるか」を宣言し、tracking-pbi / worktree /
cc-sdd / 完了後処理を一貫したシーケンスで実行する。

サイレントなフロー選択をしない。必ず宣言してから実行に入る。

---

## Step 1: PBI を読む

`docs/product-backlog.md` を読み、対象 PBI の内容と規模を把握する。

---

## Step 2: フローを選択して宣言する

実装の最初のメッセージで、選択したフローと理由を一言添える。

```
「軽量フローで進めます（ディレクトリ構造変更のみ）。
  tracking-pbi → 実装 → 完了マークの順で進めます。」
```

または

```
「フルフロー（SDD）で進めます（新機能の実装を含むため）。
  tracking-pbi → worktree → cc-sdd の順で進めます。」
```

選択したフローと理由を宣言し、ユーザーの承認を待ってから Step 3 に進む。

### フロー選択基準

**軽量フロー** — 以下をすべて満たすなら軽量を選ぶ:
- 機能追加・挙動変更がない（rename / move / パス変更 / config 調整など）
- やることが明確で仕様策定が不要
- 変更範囲が限られている（数ファイル以内の見込み）

**フルフロー（SDD）** — 以下のいずれかに該当するならフルを選ぶ:
- 新機能・新モジュールの追加
- 既存の挙動変更
- 外部サービスや API の統合
- 設計・仕様の検討が必要

迷ったらフルフローを選ぶ。

---

## Step 3: 実行する

### 軽量フロー

1. `tracking-pbi` で PBI を進行中 [~] にマーク
2. 実装:
   - main ブランチで直接作業（数分で終わる変更）
   - または短命な feature ブランチを切って作業・マージ
3. `tracking-pbi` で PBI を完了 [x] にマーク

### フルフロー（SDD）

1. `tracking-pbi` で PBI を進行中 [~] にマーク
2. `using-git-worktrees` で worktree を作成
3. cc-sdd フロー（`/kiro-spec-quick` 等）で仕様策定 → 実装
4. `finishing-a-development-branch` で PR 作成またはマージ
5. `tracking-pbi` で PBI を完了 [x] にマーク

---

## Step 4: 振り返り確認

完了後、一言添える:

```
「retrospecting-harness での振り返りを行いますか？」
```

yes なら `retrospecting-harness` を実行。no またはスキップなら終了。
