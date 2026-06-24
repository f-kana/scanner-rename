# 開発環境セットアップ

## 前提条件

- macOS
- Podman（`brew install podman`）
- VS Code + Dev Containers 拡張機能

## Podman machine の設定

DevContainer features のビルドには rootful モードが必要（rootless では `RUN --mount=type=bind` のパーミッションエラーが発生する）。

```sh
podman machine init
podman machine set --rootful
podman machine start
```

既存の machine を変更する場合:

```sh
podman machine stop
podman machine set --rootful
podman machine start
```

## DevContainer の起動

VS Code で Command Palette (Cmd+Shift+P) → `Dev Containers: Reopen in Container` を実行する。初回ビルドには数分かかる。

`postCreateCommand` で以下が自動実行される:

- `uv sync` — Python 依存パッケージのインストール
- `npm install` — Node.js 依存（Prettier 等）のインストール
- `uv run apm install` — Claude Code スキルのインストール

## Claude Code（Vertex AI 経由）

このプロジェクトでは GCP Vertex AI 上の Claude を使用する。

### ホスト側の環境変数

以下の環境変数をホストの `~/.zshrc` に設定する。DevContainer は `remoteEnv` + `${localEnv:...}` でこれらを自動的に転送する（値は `devcontainer.json` にはコミットされない）。

```sh
export CLAUDE_CODE_USE_VERTEX=1
export CLOUD_ML_REGION=us-east5
export ANTHROPIC_VERTEX_PROJECT_ID=<プロジェクトID>
```

### コンテナ内の初回認証

DevContainer 内のターミナルで以下を実行する:

```sh
gcloud auth application-default login
```

ブラウザの URL が表示されるので、ホストのブラウザにコピーして開き、SSO 認証を完了する。表示される verification code をターミナルに貼り付ける。

認証情報は named volume（`gcloud-config-*`）に保存されるため、DevContainer を rebuild しても再認証は不要。ただし、Podman machine を作り直した場合は volume が失われるので再認証が必要になる。

### 動作確認

```sh
claude
```

## Claude Code（ホスト側）

### サンドボックス設定

uv のキャッシュディレクトリへの書き込みを許可するため、ユーザーレベルの設定ファイル `~/.claude/settings.json` に以下を追加する。

```json
{
  "sandbox": {
    "permissions": {
      "filesystem": {
        "write": {
          "allow": ["~/.cache/uv"]
        }
      }
    }
  }
}
```

この設定がないと、`uv add` 等のコマンド実行時にサンドボックスが `~/.cache/uv/` への書き込みをブロックし、`dangerouslyDisableSandbox` が都度必要になる。
