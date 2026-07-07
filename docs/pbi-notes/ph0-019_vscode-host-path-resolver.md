# PBI-ph0-019: VS Code Built-in ブラウザ向け Host OS パス解決 Harness

完了日: 2026年（commit f15030b）

## なぜやったか

`skill-creator` の Eval など、Claude Code が HTML を生成して VS Code Built-in
ブラウザで目視確認したい場面がある。VS Code Built-in ブラウザは Host OS 側の
パスで動作するが、Claude Code はデフォルトで DevContainer 側のパス
（`/workspaces/...`）しか知らない。そのパスを提示してもブラウザがファイルを
開けないため、パス変換 Harness が必要だった。

## 選んだアプローチとその理由

`/proc/1/mountinfo` からワークスペースのマウント情報を取得してパス変換する
Harness（SKILL）を実装した。

理由:

- DevContainer 内では `/proc/1/mountinfo` を読むことで Host OS 側の
  マウントパスを取得できる（Mac + Podman 環境で確認済み）
- 他のスキルに依存しない自己完結した実装が必要だった

## 残った制約・注意点

- Windows + WSL + Docker 環境では `/proc/1/mountinfo` のマウント表記が
  異なる可能性があるため、動作未検証
- WSL 環境ではフォールバック処理が必要になる可能性がある
