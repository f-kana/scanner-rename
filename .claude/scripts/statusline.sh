#!/bin/bash

# Read JSON input from stdin
input=$(cat)

# Extract model info
MODEL=$(echo "$input" | jq -r '.model.display_name // "Unknown"')

# Extract effort level
EFFORT=$(echo "$input" | jq -r '.effort.level // empty')

# Extract context usage
USED_PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
USED_TOKENS=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
MAX_TOKENS=$(echo "$input" | jq -r '.context_window.context_window_size // 200000')

# Format tokens in k format (e.g., 49513 -> 49k)
USED_K=$((USED_TOKENS / 1000))
MAX_K=$((MAX_TOKENS / 1000))

# Extract cost info
TOTAL_COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
DURATION_MS=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')

# Format duration
MINS=$((DURATION_MS / 60000))
SECS=$(((DURATION_MS % 60000) / 1000))

# Extract workspace info
DIR=$(echo "$input" | jq -r '.workspace.current_dir')
DIR_BASENAME=$(basename "$DIR")

# Extract git info
branch=$(cd "$DIR" 2>/dev/null && git --no-optional-locks symbolic-ref --short HEAD 2>/dev/null || git --no-optional-locks rev-parse --short HEAD 2>/dev/null)
dirty=""
if [ -n "$branch" ] && cd "$DIR" 2>/dev/null && git --no-optional-locks ls-files --error-unmatch -m --directory --no-empty-directory -o --exclude-standard ":/*" >/dev/null 2>&1; then
    dirty=" ✗"
fi

# Build status line
printf "\033[0;35m%s\033[0m" "$MODEL"
if [ -n "$EFFORT" ]; then
    printf " \033[0;33m[⚡%s]\033[0m" "$EFFORT"
fi
printf " | %dk/%dk=%s%% | " "$USED_K" "$MAX_K" "$USED_PCT"
printf "\033[1;34m%s/\033[0m" "$DIR_BASENAME"
if [ -n "$branch" ]; then
    printf " \033[0;36m(\033[1;31m%s%s\033[0;36m)\033[0m" "$branch" "$dirty"
fi
