#!/bin/bash
set -e

# Named volume の所有権を vscode ユーザーに変更
# （初回作成時は root 所有のため）
sudo chown -R vscode:vscode /home/vscode/.claude /home/vscode/.config/gcloud

# DevContainer Feature が root でインストールした claude-code の所有権を移譲
# （vscode ユーザーが sudo なしで npm update -g できるようにするため）
sudo chown -R vscode:nvm /usr/local/share/nvm/versions/node/$(node --version)/lib/node_modules/@anthropic-ai

# tmux 設定ファイルのコピー
cp .devcontainer/.tmux.conf /home/vscode/.tmux.conf

# herdr 設定ファイルのコピー
mkdir -p /home/vscode/.config/herdr
cp .devcontainer/herdr-config.toml /home/vscode/.config/herdr/config.toml

# シェルエイリアスのコピー
cp .devcontainer/.bash_aliases /home/vscode/.bash_aliases

# Python 依存関係のインストール
uv sync

# Node.js 依存関係のインストール
npm install

# APM パッケージのインストール
uv run apm install

# Git hooks のインストール
pre-commit install
