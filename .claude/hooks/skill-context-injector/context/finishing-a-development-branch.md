## デフォルト動作

テストが通った場合、Push して Pull Request を作成する。
(`.cluade/settings.json`の設定に基づき、Push時にユーザの許可をAskすることになる)

ただし以下の場合は通常通り選択肢を提示する:
- ユーザーが明示的に別の操作を指定した場合
- main ブランチ上で作業している場合（feature ブランチがない場合）

## コミットメッセージのスコープ

PBI番号がある場合、コミットメッセージのスコープに含める。

例: `chore(PBI-ph0-010): introduce commitlint for conventional commits`
