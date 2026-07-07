# PBI-ph0-020: セキュリティ隔離モデルのドキュメント修正

完了日: 2026年（PR #10）

## なぜやったか

`docs/security-notes.md` と `docs/initial-context.md` の記述が実環境と乖離していた。

- 文書の記述: 「GCP 認証情報はホストのみに存在し、DevContainer にはマウントしない」
- 実態: `devcontainer.json` が named volume `gcloud-config-*` を
  `/home/vscode/.config/gcloud` にマウントし、ADC がコンテナ内に存在する

この乖離は PBI-ph1-001（cc-sdd Discovery）のブロッカーになっていた。
Discovery は `docs/` の事前インプットを一次参照にするため、
誤った前提で Discovery が走ることを防ぐ必要があった。

## 選んだアプローチとその理由

ドキュメントを実態に合わせて書き直し、受容済みリスクとして明文化した。

採用したモデル:
「ADC はコンテナ内に存在するが、settings.json の deny リストと規範ルールで
Claude Code からの読み取りを抑止する（受容済みリスク）」

あわせて以下を明文化:

- deny リストは列挙式のベストエフォートであり、完全な技術的強制ではない
- 防御の主軸はブローカー設計・gitleaks・レビューである

## 却下した代替案

ADC をコンテナ内にマウントしない構成に戻す案は却下した。理由:

- Claude Code 自身の Vertex AI 認証（会社契約の GCP Vertex 経由）に
  コンテナ内の ADC が必要
- マウントを外すと Claude Code が動作しなくなる

## 残った制約・注意点

- クラウド統合テストをブローカー経由に限定する方針自体は変更していない
- deny リストはファイルパスの列挙であり、パスが変わると効かなくなる可能性がある
