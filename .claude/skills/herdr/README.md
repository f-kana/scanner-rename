# herdr

取得元: `https://raw.githubusercontent.com/ogulcancelik/herdr/master/SKILL.md`

取得時 commit: `b04c6496`

## APM を使わない理由

herdr は APM パッケージとして設計されていない（リポジトリに `apm.yml` がない）。
`apm install ogulcancelik/herdr` を実行すると Rust ソース・ベンダーコード・GitHub Actions ワークフローを含む 1400 ファイル以上が混入するため、SKILL.md 単体を curl で取得している。

更新する場合は同じ URL から curl で上書きすること。
