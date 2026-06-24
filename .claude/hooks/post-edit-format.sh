#!/bin/bash
# PostToolUse hook: Auto-format edited files
# Runs after Edit/Write/NotebookEdit tool execution
# - Python files: ruff format
# - Markdown/JSON/YAML: prettier --write

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name')
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')

# Only process Edit/Write/NotebookEdit
if [[ "$TOOL" != "Edit" && "$TOOL" != "Write" && "$TOOL" != "NotebookEdit" ]]; then
  exit 0
fi

# File path must be present
if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  exit 0
fi

# Format based on file extension
case "$FILE" in
  *.py)
    uv run ruff format "$FILE" >/dev/null 2>&1 || true
    ;;
  *.md|*.json|*.yaml|*.yml)
    npm exec --no -- prettier --write "$FILE" >/dev/null 2>&1 || true
    ;;
esac

exit 0
