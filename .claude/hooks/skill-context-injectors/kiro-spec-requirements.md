# kiro-spec-requirements Context Injection

## 日本語ローカライズ

spec.json の language が "ja" の場合、以下のルールを適用する:

- Requirement見出しは日本語にする（例: `Requirement 1: コミット時のシークレット検出`）
- Objective（User Story）は日本語で記述する。"As a ... I want ... so that ..." パターンは使わず、自然な日本語で書く（例: `開発者として、〜を望む。それにより〜`）
- EARS acceptance criteria では、EARSキーワード（When, If, While, Where, The [system] shall）は英語のまま、変数部分（イベント、アクション、条件）は日本語にする
- Boundary Context（In scope, Out of scope, Adjacent expectations）の内容も日本語にする
- Introduction は日本語で記述する
