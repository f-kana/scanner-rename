# kiro-spec-requirements Context Injection

## 日本語ローカライズ

spec.json の language が "ja" の場合、以下のルールを適用する:

- Requirement見出しは日本語にする（例: `Requirement 1: コミット時のシークレット検出`）
- Objective（User Story）は日本語で記述する。"As a ... I want ... so that ..." パターンは使わず、自然な日本語で書く（例: `開発者として、〜を望む。それにより〜`）
- EARS acceptance criteria では、EARSキーワード（When, If, While, Where, The [system] shall）は英語のまま、変数部分（イベント、アクション、条件）は日本語にする
- Boundary Context（In scope, Out of scope, Adjacent expectations）の内容も日本語にする
- Introduction は日本語で記述する

## ユーザーレビューポイントの提示

Requirements 生成後の出力に「レビューポイント」セクションを含める。以下を抽出して提示する:

- 複数の解釈が可能な要件（Design フェーズでどちらにも転びうる箇所）
- 既存の構成からの変更を伴う要件（ディレクトリ移動、ツール削除・追加など）
- トレードオフがある選択（パフォーマンス vs 安全性、利便性 vs 制約など）

レビューポイントがない場合は「特になし」と明記する。「Design 生成に進みますか？」の前に表示する。
