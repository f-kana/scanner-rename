---
name: curating-harness
description: >-
  Claude Codeハーネスの構成要素（Skill、SubAgent、Hook、slash command、MCP、Plugin、CI template等）について、
  公開済み候補の調査と採用判断を行う。Fit（要求適合度）、Trust（信頼性）、Risk（supply-chain risk）の
  3軸で評価し、そのまま採用・fork/vendor・参考にして自作・完全自作・不採用を決定する。
  classifying-harnessで修正先が分類された後、外部調達・自作判断が必要な場合に起動する。
  このスキルを使うべき場面: 新規Skill/Hook/SubAgent/MCP等の導入検討、既存公開物の採用可否判断、
  supply-chain riskの評価、APM/Plugin候補の選定。
  Skill・SubAgent・Hook等の新規導入や既存公開物の評価が話題に出たら、このスキルで判断せよ。
---

# Curating Harness

Claude Codeハーネスの構成要素について、既存公開物を採用すべきか自作すべきかを判断するスキル。
単なる検索ではなく、要求適合度・信頼性・保守性・導入方式・supply-chain riskを踏まえて採用判断を行う。

## 位置付け

`curating-harness` は `classifying-harness` の後段で使う。

典型的な流れ:

1. `classifying-harness` で問題を解くべきレイヤーを分類する
2. 分類結果が外部調達の対象であれば、`curating-harness` で候補を探す
3. 候補の適合度・信頼性・リスクを評価する
4. そのまま採用、fork/vendor、参考にして自作、完全自作、不採用を判断する
5. 導入方法を提案する

CLAUDE.mdへの追記可否やpath-scoped rule等の修正先分類は `classifying-harness` の責務であり、このスキルの対象外。

## 核心原則

公開物を探す前に、まず `classifying-harness` の分類結果を確認する。

分類が未了の場合は、原則として `classifying-harness` を先に実施する。分類結果が曖昧な場合は独断で検索に進まず、まず分類仮説を置いてから探索する。

## 対象範囲

対象:

- Claude Code Skill / SubAgent / Hook / slash command
- MCP server / Claude Code Plugin / APM package
- CI/CD template / DevContainer補助設定
- テスト・レビューHarness / Agent workflow
- 外部Skillのカスタマイズ方法

対象外:

- 一回限りのプロンプト改善
- ユーザー個人のメモリ
- 単なるCLAUDE.md追記判断
- プロジェクト固有すぎる業務ルールの一般公開物検索
- 安全性を確認できない野良コードの直接導入

## ワークフロー

### Step 1: 入力要求の整理

ユーザーの要求を以下の観点で整理する。

- 欲しいもの / 解決したい問題
- `classifying-harness` の分類結果（または分類仮説）
- 想定レイヤー（Skill / SubAgent / Hook / MCP等）
- チーム共有の必要性
- 外部ツール/API接続の必要性
- 強制力の必要性
- セキュリティ上の懸念

分類結果が曖昧な場合の例:

```
分類仮説:
- 主分類: Skill
- 副分類: SubAgent
- 理由: 複数ステップの再利用可能ワークフローであり、独立レビュー観点も必要になる可能性がある
```

### Step 2: 探索対象の決定

分類結果に応じて探索対象を決める。

| 分類 | 主な探索対象 |
|------|------------|
| Skill | Claude Skills, Plugin Marketplace, APM, GitHub |
| SubAgent | Claude Code agents, Plugin Marketplace, GitHub |
| Hook | Claude Code hooks, GitHub, CI template |
| slash command | Claude Code commands, prompt collections, GitHub |
| MCP | MCP Registry, official vendor MCP, GitHub |
| Plugin | Claude Code Plugin Marketplace, APM |
| CI/Test Harness | GitHub Actions templates, official docs, trusted repos |
| DevContainer | official devcontainer features/templates, trusted repos |

以下に該当する場合は探索不要。理由を明示して自作または既存ハーネス内修正を推奨する:

- path-scoped ruleやCLAUDE.mdの短い変更で十分
- 一回限りの文脈
- プロジェクト固有の業務ルールで公開物の再利用性が低い

### Step 3: 信頼できる探索元の優先

探索元は信頼度順に使う。

優先度A（公式・準公式）:
- Claude Code Plugin Marketplace
- Anthropic official skills / official examples
- Microsoft APM
- Model Context Protocol official registry
- vendor公式repo（OpenAI、Microsoft、GitHub等）
- 利用対象ツールの公式ドキュメント

優先度B（有力Organization・広く使われている公開物）:
- GitHub上の有力organization（Cloudflare、Vercel、Google等）
- Star数・fork数・issue処理状況・更新頻度が十分なrepo
- mcpservers.org等のカタログ（導入元としてではなく探索入口として扱う）

優先度C（個人repo・awesome list・ブログ由来）:
- 原則として直接採用しない
- 設計・アイデアの参考に留める
- 採用する場合はfork/vendorしてレビューする

### Step 4: 候補検索

検索時は、機能名・類義語・対象ツール・分類レイヤーの観点で検索語を複数作る。

検索結果は候補リストとして整理する:

| 候補 | 種別 | 出所 | 概要 | 初期評価 |
|------|------|------|------|---------|
| candidate-a | Hook | official | 完了通知hook | 評価対象 |
| candidate-b | Skill | GitHub/個人 | 通知設定手順 | 参考程度 |

候補が見つからない場合でも、検索語・探索元・見つからなかった理由を記録する。

### Step 5: 要求適合度（Fit）の評価

各候補について要求適合度を評価する。

| Fit | 基準 |
|-----|------|
| High | 要求の80%以上を満たし、追加修正が小さい |
| Medium | 要求の50〜80%を満たすが、修正・補完が必要 |
| Low | 一部の設計思想や部品だけ参考になる |
| None | 要求に合わない |

評価観点:
- 解決したい問題に直接対応しているか
- Claude Codeで自然に使えるか
- 日本語/プロジェクト固有ルールを注入しやすいか
- 既存の `classifying-harness` や `retrospecting-harness` と競合しないか
- 運用者が理解・保守できるか

### Step 6: 信頼性・保守性（Trust）の評価

各候補について以下を確認する。

確認項目:
- Publisherは公式/有力か
- 最終更新日・過去2年の更新頻度
- Star/fork等の利用実績
- issue/PRの処理状況
- license、README、install手順の明確さ
- version pin / commit SHA pinの可否

| Trust | 基準 |
|-------|------|
| High | 公式/有力publisher、更新あり、利用実績あり、導入手順明確 |
| Medium | 一定の利用実績はあるが、更新・issue・導入手順に懸念あり |
| Low | 個人repo、更新不明、利用実績が乏しい |
| Unknown | 情報不足 |

LowまたはUnknownの場合、直接採用を避ける。

### Step 7: セキュリティ・supply-chain risk（Risk）の評価

以下を含む候補はリスクを高く見る:
- install script / shell script実行
- Hook追加 / MCP server起動
- 外部通信 / credential・token読み取り
- ファイルの広範囲読み書き / git操作
- package manager経由の大量依存追加
- prompt injection / role override / 「他の指示を無視せよ」系の文言
- 出所不明binary / 目的に比べて広すぎる権限要求

| Risk | 基準 |
|------|------|
| Low | 自然言語手順中心、外部通信なし、権限小 |
| Medium | scriptや依存があるが限定的で監査可能 |
| High | hook/MCP/外部通信/credential/広範囲ファイル操作を含む |
| Critical | 悪性指示、権限過大、出所不明binary、credential収集の疑い |

重要: 「悪意・脆弱性がない」と断定しない。「許容可能なリスク水準か」で判断する。High以上は直接導入せず、必要ならsandbox検証・fork/vendor・権限制限を前提にする。

### Step 8: 採用判断

Fit、Trust、Riskを組み合わせて判断する。

| Fit | Trust | Risk | 推奨判断 |
|-----|-------|------|---------|
| High | High | Low | そのまま採用候補 |
| High | High | Medium | fork/vendorまたは限定導入 |
| High | Medium | Low/Medium | fork/vendorして採用 |
| Medium | High | Low | fork/vendorまたはskill-context-injectorで補正 |
| Medium | Medium | Low/Medium | 参考にして自作 |
| Low | Any | Any | 原則自作 |
| Any | Low | Medium/High | 直接採用しない。参考にして自作 |
| Any | Any | High | 原則不採用。必要ならsandbox検証 |
| Any | Any | Critical | 不採用 |

採用判断は以下のいずれかに限定する:

1. そのまま採用
2. fork/vendorして採用
3. skill-context-injectorで補正して採用
4. 参考にして自作
5. 完全自作
6. 不採用
7. 追加調査が必要

自作推奨の目安:
- 要求がプロジェクト固有
- 既存候補のFitがMedium未満、TrustがLow/Unknown、RiskがHigh以上
- 候補の理解・監査コストが自作より高い
- 日本語運用・社内ルール注入が中心
- upstream更新で挙動が変わると困る

既存採用/fork推奨の目安:
- 公式/有力publisherが提供、FitがHigh
- RiskがLowまたは監査可能なMedium
- APM/Pluginでバージョン固定可能
- チーム全体で同じものを使う価値がある

### Step 9: 導入方法の提案

導入方法は以下の優先順位で検討する。

1. Claude Code Plugin Marketplace: 公式/信頼できるPluginがある場合に優先。チーム標準にする場合はバージョン・権限・更新方針を明確にする。

2. APM: `apm.yml` がある場合や、チーム配布・バージョン固定・lockfileが必要な場合に優先。

3. fork/vendor: 公式ではないが有用、修正が必要、upstream更新をそのまま受けたくない、監査済み状態を固定したい場合に優先。

4. skill-context-injector: APM等で導入した外部Skillの挙動だけを補正したい場合。SKILL.mdを直接編集せず、PJ固有の小さなコンテキストを注入する。

5. 手動配置: `curl`で取得してファイルを直接作成する方法は最終手段。使う場合は取得元URL・commit SHA/tag・license・変更差分・レビュー者を記録する。

## SubAgent利用方針

複雑な調査ではSubAgentを分けるとよい。

推奨ロール:
- 検索Agent: 公式・準公式ソースとGitHubを分けて検索
- 適合度評価Agent: 要求との適合度を評価
- セキュリティ評価Agent: script、hook、MCP、外部通信、credential、prompt injection riskを評価
- 統合判断Agent: 各Agentの結果を統合して採用判断を出す

注意: 検索Agentとセキュリティ評価Agentを同じにしない（検索Agentは候補を見つける方向にバイアスがかかる）。安全性は断定せず許容可能リスクとして扱う。

## 関連スキル・ツールとの関係

- `classifying-harness`: 前段。どのレイヤーで解くべきかを分類する。分類後に本スキルが起動する。
- `retrospecting-harness`: セッション後の振り返りで改修提案を作る。提案がSkill/Hook等の新規導入を含む場合に本スキルが使われる。
- skill-context-injector: 外部SkillのSKILL.mdを直接編集せず挙動を補正する手段。本スキルの導入方法の一つ。
- APM: 採用後の固定・配布・再現性確保に使う。本スキルは「何を採用するか」を判断し、APMは「採用したものを管理する」役割。

## 禁止・注意事項

- 野良Skillを見つけて即installしない
- curl pipe shellを推奨しない
- 出所不明binaryを導入しない
- install scriptやhookを読まずに導入しない
- MCP serverの権限を確認せずに導入しない
- credentialやtokenを読む候補を軽く扱わない
- 「悪意がない」と断定しない
- Star数だけで信用しない
- awesome listを信頼済み導入元として扱わない
- upstream更新を自動で受ける構成にしない
- CLAUDE.mdに調達判断ロジックを詰め込まない

## 判断例

### 良い例: 完了通知Hook

要求: Claude Codeの長時間処理完了時にMac通知と音を出したい。

判断:
- 分類: Hook
- 既存候補が公式/有力でFit Highなら採用
- 個人repoのshell scriptなら、fork/vendorして内容確認
- 自作が簡単なら、既存を参考に小さく自作

推奨: 小さいhookで済むため、野良repoを直接導入するより自作またはvendor管理がよい。

### 良い例: レガシーモダナイゼーションのCharacterization Test Skill

要求: 旧システムの挙動をGolden Master Testとして固定するSkillが欲しい。

判断:
- 分類: Skill + possibly SubAgent
- 既存候補は参考になるがPJ固有性が高い
- テスト対象・旧システム接続・データマスキング・期待値生成がPJ依存

推奨: 既存候補は参考にして、自作Skillを推奨。

### 悪い例

「GitHubでStarが多いので、そのままcurlで導入する」
問題: 権限・script・license・更新状況・導入固定が未確認。チーム共有Harnessとして危険。

「分類せずにSkillを探す」
問題: 本当はHook/CIで強制すべき問題をSkillにしてしまう。本当はpath-scoped ruleで足りる問題を過剰設計する。

## 出力形式

通常の回答では `references/output-templates.md` のテンプレートに従って出力する。

## 完了条件

このスキルの出力は以下を満たすこと:

- `classifying-harness` の分類結果を前提にしている
- 候補を探す場合、探索元を明示している
- Fit / Trust / Risk を分けて評価している
- 「そのまま採用」「fork/vendor」「参考にして自作」「完全自作」「不採用」のいずれかを明示している
- 導入方法を提案している
- 直接導入のリスクを明示している
- 自作する場合は最小構成の骨子を提示している
- 不確実な点は不確実として扱っている
