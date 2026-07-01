#!/bin/bash
# PostToolUse hook: Auto-format edited files
# Runs after Edit/Write/NotebookEdit tool execution
# Delegates to pre-commit for unified formatting configuration

set -euo pipefail
shopt -s nocasematch  # Case-insensitive file extension matching

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null || echo "")

# File path must be present and exist
[[ -z "$FILE" || ! -f "$FILE" ]] && exit 0

# Run pre-commit hooks on the file
# - Unified configuration in .pre-commit-config.yaml
# - Security hooks (gitleaks) block on failure
# - Formatter hooks (ruff, prettier) are non-blocking (they auto-fix)
OUTPUT=$(uv run pre-commit run --files "$FILE" 2>&1) || {
  if echo "$OUTPUT" | grep -qi "gitleaks.*failed"; then
    jq -n --arg reason "gitleaks detected a potential secret in $FILE. Review and remove the secret before proceeding." \
      '{decision: "block", reason: $reason}'
    exit 0
  fi
}

exit 0
