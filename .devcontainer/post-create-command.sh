#!/bin/bash
set -e

# Named volume の所有権を vscode ユーザーに変更
# （初回作成時は root 所有のため）
sudo chown -R vscode:vscode /home/vscode/.claude /home/vscode/.config/gcloud

# tmux のインストール
sudo apt-get update
sudo apt-get install -y tmux

# tmux 設定ファイルのコピー
cp /workspaces/scanner-rename-initial-docs/.devcontainer/.tmux.conf /home/vscode/.tmux.conf

# Python 依存関係のインストール
uv sync

# Node.js 依存関係のインストール
npm install

# APM パッケージのインストール
uv run apm install
