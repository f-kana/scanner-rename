## name フィールドの制約

以下は YAML frontmatter の name フィールドのみに適用する。description フィールドでは具体的なツール名やサービス名を積極的に使ってよい。

name フィールドには技術的制約がある：

- 最大64文字
- 小文字の英字・数字・ハイフンのみ使用可能
- `anthropic`, `claude` は予約語のため使用禁止

命名スタイルは動名詞形（gerund form）(+目的語)を第一候補にする。スキルが「何をする活動か」が一目でわかるため。

良い例：
- `processing-pdfs`
- `analyzing-spreadsheets`
- `managing-databases`
- `reviewing-code`
- `tracking-pbi`

許容される代替形：
- 名詞句: `pdf-processing`, `spreadsheet-analysis`
- 動詞句: `process-pdfs`, `analyze-spreadsheets`

避けるべきパターン：
- 曖昧: `helper`, `utils`, `tools`
- 汎用すぎ: `documents`, `data`, `files`
- パターンの不統一（同一コレクション内で動名詞と名詞句が混在する等）

許容されるその他の形式：
- -workflow: 複数のSKILLやSubagentを実行する手順を記載している（例：deploy-workflow）

## description フィールドの制約

- 最大1024文字
- 空文字は不可
- XMLタグを含めてはならない
- 一人称（I, we）・二人称（you）の代名詞を使わない。既存スキルの imperative style（"Create...", "Analyze..."）に合わせる。description はシステムプロンプトに注入されるため、視点の不一致はスキル選択の精度を下げる
- description の言語はリポジトリ内の自作スキルに合わせる。自作か外部導入かは以下のマーカーで判別する（いずれかに該当すれば外部導入、どれにも該当しなければ自作）：
  - `apm.yml` の `dependencies.apm` に記載されている
  - `.claude/settings.json` の `enabledPlugins` に記載されている
  - `.claude/skills/<name>` がシンボリックリンクである（`npx skills add` のデフォルト挙動）
  - `skills-lock.json` に記載されている
