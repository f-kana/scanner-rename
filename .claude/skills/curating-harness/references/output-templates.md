# 出力テンプレート

## 候補がある場合

```markdown
# Harness curation result

## 1. 要求整理

- 欲しいもの:
- 解決したい問題:
- classifying-harness分類:
- 探索対象:

## 2. 候補

| 候補 | 種別 | 出所 | Fit | Trust | Risk | コメント |
|------|------|------|-----|-------|------|---------|

## 3. 推奨判断

結論:

理由:

## 4. 導入方法

推奨導入:

手順概要:

## 5. 自作する場合の骨子

- name:
- description:
- 主な責務:
- 対象外:
- 必要なresources/scripts:
- eval観点:
```

## 候補がない場合

```markdown
# Harness curation result

## 1. 結論

有力な公開候補は見つからない。
自作を推奨する。

## 2. 探索した範囲

- Claude Code Plugin Marketplace:
- Anthropic official skills:
- Microsoft APM:
- MCP Registry:
- GitHub:
- その他:

## 3. 自作を推奨する理由

- 要求がPJ固有
- 既存候補はFitが低い
- 既存候補はTrust/Riskに懸念
- 小さく自作した方が保守しやすい

## 4. 自作Skill/Agent/Hook案

- name:
- description:
- workflow:
- resources:
- scripts:
- eval:
```
