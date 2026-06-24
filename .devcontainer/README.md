# DevContainer 設定

## 概要

開発は DevContainer 内で行う。Claude Code も DevContainer 内で実行する。

## 設計判断と経緯

### Podman rootful モードが必要な理由

DevContainer features は内部的に `RUN --mount=type=bind` を使う Dockerfile を生成する。Podman の rootless モードでは、ユーザー名前空間の UID マッピングにより bind mount されたファイルにビルド時アクセスできず、全 feature が `Permission denied` で失敗する（[devcontainers/features#755](https://github.com/devcontainers/features/issues/755)）。`runArgs` の `--userns=keep-id` は `podman run`（実行時）にしか効かず、`podman build` には無関係。

対策として `podman machine set --rootful` でビルドを rootful にしている。

### gcloud CLI を Dockerfile で直接インストールしている理由

公式の DevContainer feature は存在しない。コミュニティ feature（`ghcr.io/dhoeric/features/google-cloud-cli`）は廃止された `apt-key` コマンドに依存しており、現行の Debian ベースイメージでは `apt-key: command not found` で失敗する。Google 公式の apt リポジトリ手順（signed-by keyring 方式）で直接インストールしている。

### uv を COPY --from でインストールしている理由

当初は `curl -LsSf https://astral.sh/uv/install.sh | sh` を使っていたが、このスクリプトは実行ユーザーの `$HOME/.local/bin` にインストールする。Dockerfile の RUN は root で実行されるため `/root/.local/bin` に入るが、`remoteUser: vscode` の PATH（`/home/vscode/.local/bin`）とは不一致で `uv: not found` になった。uv 公式推奨の Docker パターンである `COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/` に変更し、どのユーザーからもアクセス可能にした。

### Claude Code のインストールを feature に変更した理由

当初は `postCreateCommand` で `npm install -g @anthropic-ai/claude-code` していたが、Anthropic 公式の DevContainer feature（`ghcr.io/anthropics/devcontainer-features/claude-code:1.0`）が提供されており、VS Code 拡張の自動追加や自動更新も含まれるため、feature に移行した。

### APM を Python dev dependency にした理由

APM（Agent Package Manager）は npm パッケージではなく、PyPI の `apm-cli` で提供されている。`npx apm install` は動作しない。`pyproject.toml` の dev dependency に追加することで `uv sync` で自動インストールされ、バージョンも `uv.lock` でピン留めされる。

### named volume でホスト認証情報をマウントしない理由

プロジェクトのセキュリティ方針（`docs/security-notes.md`）により、ホストの `~/.config/gcloud/` はコンテナにマウントしない。Claude Code 公式ドキュメントも「ホストのクラウド認証ファイルのマウントを避ける」と推奨している。代わりにコンテナ内で `gcloud auth application-default login` を実行し、named volume で永続化することで rebuild 後の再認証を不要にしている。

### postCreateCommand 先頭の sudo chown の理由

named volume は初回作成時に root 所有で作成される。`remoteUser: vscode` で実行される `gcloud auth` や Claude Code がこれらのディレクトリに書き込めるよう、所有権を修正している。
