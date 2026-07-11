#!/bin/bash
# PostToolUse hook: VS Code Built-in ブラウザ向け Host OS パス解決
#
# Write ツールで tmp/**/*.html または docs/**/*.html を書いた直後に発火する。
# VS Code の Built-in ブラウザは Host OS 側のパスで動作するため、
# DevContainer パスをそのまま提示してもブラウザが開けない。
# このフックが Host OS 側の等価パスを出力し、Claude がユーザーに伝える。
#
# 動作確認済み環境:
#   - Mac/Linux + Podman/Docker DevContainer (/proc/1/mountinfo 経由)
# 動作未検証環境:
#   - Windows + WSL + Docker (LOCAL_WORKSPACE_FOLDER または /proc/1/mountinfo 経由)

set -euo pipefail

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null || echo "")

# tmp/**/*.html と docs/**/*.html 以外は対象外
[[ -z "$FILE" ]] && exit 0
[[ "$FILE" != */tmp/*.html && "$FILE" != */tmp/**/*.html && "$FILE" != */docs/*.html && "$FILE" != */docs/**/*.html ]] && exit 0
[[ ! -f "$FILE" ]] && exit 0

# Host OS パスを解決する
host_path=""

# 戦略1: LOCAL_WORKSPACE_FOLDER（一部の VS Code Remote Container 構成で設定される）
if [[ -n "${LOCAL_WORKSPACE_FOLDER:-}" ]]; then
  container_workspace="${CLAUDE_PROJECT_DIR:-}"
  if [[ -n "$container_workspace" ]]; then
    relative="${FILE#"$container_workspace"}"
    host_path="${LOCAL_WORKSPACE_FOLDER}${relative}"
  fi
fi

# 戦略2: /proc/1/mountinfo（virtiofs / bind マウント）
if [[ -z "$host_path" && -r /proc/1/mountinfo ]]; then
  container_workspace="${CLAUDE_PROJECT_DIR:-}"
  if [[ -n "$container_workspace" ]]; then
    # マウントポイントがワークスペースに一致するエントリを探す
    # フォーマット: mountID parentID major:minor root mountpoint options ... - fstype source options
    while IFS= read -r line; do
      mountpoint=$(echo "$line" | awk '{print $5}')
      root=$(echo "$line" | awk '{print $4}')
      if [[ "$container_workspace" == "$mountpoint" || "$container_workspace" == "$mountpoint"/* ]]; then
        # host path = root + (マウントポイントからの相対パス)
        relative_to_mount="${container_workspace#"$mountpoint"}"
        host_root="${root%/}"
        relative_file="${FILE#"$mountpoint"}"
        host_path="${host_root}${relative_to_mount}${relative_file}"
        break
      fi
    done < /proc/1/mountinfo
  fi
fi

# 解決できなかった場合はサイレントスキップ（DevContainer 外、または未対応のマウント形式）
[[ -z "$host_path" ]] && exit 0

echo "HOST_PATH: ${host_path}"
