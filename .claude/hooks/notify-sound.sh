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

if [[ "$TYPE" == "notify" ]]; then
    printf '\a'
    sleep 0.3
    printf '\a'
    sleep 0.3
    printf '\a'
else
    printf '\a'
fi

exit 0
