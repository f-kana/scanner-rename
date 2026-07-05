#!/bin/bash
# Stop / Notification フック: タスク状態変化をターミナルベルで通知する
#
# サブコマンド (settings.json のフックから呼び出す):
#   notify-sound.sh start   — セッション開始時刻を記録 (UserPromptSubmit フック)
#   notify-sound.sh stop    — 経過時間がしきい値以上の場合のみベル (Stop フック)
#   notify-sound.sh notify  — 即時トリプルベル (Notification/permission_prompt フック)
#
# 設定 ($HOME に置くオプションファイル):
#   ~/.claude_bell_tty  — 登録済みターミナルパス; セッションごとに `make setup-bell` を実行
#
# ターミナル検出の優先順位:
#   1. ~/.claude_bell_tty  — ユーザー登録済みターミナル (ターミナルマルチプレクサ必須)
#   2. プロセスツリー探索  — 祖先プロセスの最初の pts を探す (シンプルな環境で有効)
#   3. stderr フォールバック — 最終手段

set -euo pipefail

# ---- 設定値 ----
# Stop でベルを鳴らす最小経過秒数
THRESHOLD_SEC=60
# ----------------

TYPE=${1:-stop}
REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
STATE_DIR="$REPO_ROOT/tmp/claude-notify"

# フック JSON から session_id を読み取る (全フック種別で stdin に JSON が来る)
SESSION_ID=$(jq -r '.session_id // empty' 2>/dev/null || true)

find_terminal() {
    local cfg="$HOME/.claude_bell_tty"
    if [[ -f "$cfg" ]]; then
        local tty_path
        tty_path=$(tr -d '[:space:]' < "$cfg")
        if [[ -w "$tty_path" ]]; then
            echo "$tty_path"
            return 0
        fi
    fi

    # 注意: ターミナルマルチプレクサ (wezterm/tmux/zellij) 環境では、
    # マルチプレクサが管理する内側の pts が見つかり、VS Code 外側ターミナルとは異なる。
    # その場合は make setup-bell で正しいターミナルを登録すること。
    local pid=$$
    for _ in $(seq 1 20); do
        local fd0
        fd0=$(readlink "/proc/$pid/fd/0" 2>/dev/null)
        if [[ "$fd0" == /dev/pts/* ]]; then
            echo "$fd0"
            return 0
        fi
        pid=$(awk '/^PPid:/{print $2}' "/proc/$pid/status" 2>/dev/null)
        [[ -z "$pid" || "$pid" == "0" || "$pid" == "1" ]] && break
    done

    return 1
}

TERMINAL=$(find_terminal || true)

bell() {
    if [[ -n "$TERMINAL" && -w "$TERMINAL" ]]; then
        printf '\a' > "$TERMINAL"
    else
        printf '\a' >&2
    fi
}

case "$TYPE" in
    start)
        [[ -z "$SESSION_ID" ]] && exit 0
        mkdir -p "$STATE_DIR"
        date +%s > "$STATE_DIR/${SESSION_ID}.start"
        ;;
    stop)
        [[ -z "$SESSION_ID" ]] && exit 0
        start_file="$STATE_DIR/${SESSION_ID}.start"
        [[ -f "$start_file" ]] || exit 0
        start_time=$(cat "$start_file")
        elapsed=$(( $(date +%s) - start_time ))
        rm -f "$start_file"
        [[ "$elapsed" -ge "$THRESHOLD_SEC" ]] && bell
        ;;
    notify)
        # パーミッションプロンプトは経過時間に関わらず常に通知する
        bell; sleep 0.3; bell; sleep 0.3; bell
        ;;
esac

exit 0
