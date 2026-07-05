#!/bin/bash
# Stop / Notification hook: Play terminal bell to signal task state changes
#
# Usage:
#   notify-sound.sh stop    — single bell (LLM processing done)
#   notify-sound.sh notify  — triple bell (awaiting human approval)
#
# Falls back to single bell when TYPE is unrecognized.
# Reads stdin to satisfy hook protocol, but ignores the content.

set -euo pipefail

TYPE=${1:-stop}
cat > /dev/null  # consume stdin (hook protocol requires reading it)

# /dev/tty: controlling terminal (available when Claude Code runs in a terminal)
# stderr: fallback in case /dev/tty is unavailable
bell() { printf '\a' > /dev/tty 2>/dev/null || printf '\a' >&2; }

if [[ "$TYPE" == "notify" ]]; then
    bell; sleep 0.3; bell; sleep 0.3; bell
else
    bell
fi

exit 0
