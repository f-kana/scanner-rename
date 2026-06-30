# kiro-spec-quick Context Injection

## Spec ディレクトリの命名規約

PBI に紐づく spec を作成する場合、feature-name に PBI 番号をプレフィクスとして含める。

- 形式: `{pbi-番号}-{feature-name}`（例: `ph0-009-secret-scanning`）
- PBI 番号は会話コンテキストから取得する（tracking-pbi で進行中のPBI、またはユーザーの指示から）
- PBI に紐付かない spec（discovery 起点等）の場合はプレフィクスなしでよい
