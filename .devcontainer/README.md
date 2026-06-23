# DevContainer 設定

## 概要

開発は DevContainer 内で行う。Claude Code も DevContainer 内で実行する。

## 設計意図

### セキュリティ隔離

GCP 認証情報はホスト上のみに存在し、DevContainer にはマウントしない。クラウド統合テストは DevContainer から直接 Google API を呼ばず、ホスト上の GCP Test Broker（`host.containers.internal:8765`）経由で実行する。詳細は `docs/security-notes.md` と `docs/adr-candidates/0004-devcontainer-and-gcp-test-broker.md` を参照。

### コンテナランタイム

Podman（podman machine）を使用する。Docker でも動作するが、`dev.containers.dockerPath` の設定は各自の VS Code User settings で行う。リポジトリの `.vscode/settings.json` にはランタイム固有の設定を入れない。

Podman rootless ではファイル権限の問題を防ぐため `--userns=keep-id` を `runArgs` で指定している。

### VS Code 拡張機能の配置

ホスト側の `.vscode/extensions.json` には Remote Containers 拡張のみを置く。開発用拡張（Python, Ruff, Pylance, Prettier 等）は `devcontainer.json` の `customizations.vscode.extensions` で管理し、DevContainer 内に自動インストールされる。

### uv のインストール

Astral 公式のインストールスクリプトを Dockerfile で実行する。コミュニティ製の DevContainer feature や pip 経由ではなく、公式スクリプトを採用した。Dockerfile で `ENV PATH` を設定し、非インタラクティブシェルでも `uv` コマンドが使えるようにしている。

### Claude Code CLI

Node.js は DevContainer features 経由でインストールされるため Dockerfile のビルド時にはまだ使えない。そのため Claude Code CLI は `postCreateCommand` でグローバルインストールする。

### 依存関係の自動セットアップ

`postCreateCommand` で `uv sync && npm install && npx apm install && npm install -g @anthropic-ai/claude-code` を実行し、コンテナ作成直後から開発可能な状態にする。

### タイムゾーン

日本でのみ使用するシステムのため `TZ=Asia/Tokyo` を設定している。

## 環境変数

| 変数名 | 用途 | デフォルト値 |
| --- | --- | --- |
| `GCP_TEST_BROKER_URL` | GCP Test Broker の接続先 | `http://host.containers.internal:8765` |
| `TZ` | タイムゾーン | `Asia/Tokyo` |
