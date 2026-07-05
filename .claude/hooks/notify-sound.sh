#!/bin/bash
# Stop / Notification hook: Play terminal bell to signal task state changes
#
# Subcommands (called by hooks in settings.json):
#   notify-sound.sh start   — record session start time (UserPromptSubmit hook)
#   notify-sound.sh stop    — ring bell only if elapsed >= threshold (Stop hook)
#   notify-sound.sh notify  — triple bell immediately (Notification/permission_prompt hook)
#
# Configuration (optional files in $HOME):
#   ~/.claude_bell_tty  — registered terminal path; run `make setup-bell` once per session
#
# Terminal detection strategy (in priority order):
#   1. ~/.claude_bell_tty  — user-registered terminal (required with terminal multiplexers)
#   2. Process tree walk   — finds first pts in ancestry (works in simple environments)
#   3. stderr fallback     — last resort

set -euo pipefail

TYPE=${1:-stop}
STATE_DIR="$HOME/.claude-notify"

# Read session_id from hook JSON (all hook types receive JSON on stdin)
SESSION_ID=$(jq -r '.session_id // empty' 2>/dev/null || true)

# Minimum elapsed seconds before Stop rings (edit this script to change)
THRESHOLD=5

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

    # Note: with terminal multiplexers (herdr/tmux/zellij), this finds the inner pts
    # managed by the multiplexer — not the outer VS Code terminal. In that case,
    # register the correct terminal with: make setup-bell
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
        [[ "$elapsed" -ge "$THRESHOLD" ]] && bell
        ;;
    notify)
        # Permission prompts always notify regardless of elapsed time
        bell; sleep 0.3; bell; sleep 0.3; bell
        ;;
esac

exit 0
