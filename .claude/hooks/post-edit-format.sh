#!/bin/bash
# PostToolUse hook: Auto-format edited files
# Runs after Edit/Write/NotebookEdit tool execution
# Delegates to pre-commit for unified formatting configuration

set -euo pipefail
shopt -s nocasematch  # Case-insensitive file extension matching

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')

# File path must be present and exist
[[ -z "$FILE" || ! -f "$FILE" ]] && exit 0

# Run pre-commit hooks on the file
# - Unified configuration in .pre-commit-config.yaml
# - stderr visible for debugging, but hook failure doesn't block Claude
uv run pre-commit run --files "$FILE" 2>&1 || true

exit 0
