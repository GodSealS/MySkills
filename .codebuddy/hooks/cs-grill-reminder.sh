#!/bin/bash
# cs-grill-reminder.sh — PostToolUse hook for Write|Edit (CodeBuddy)
# Detects design doc writes and suggests running grill-me to stress-test the design.
# Dependencies: jq (optional, falls back gracefully)

set -euo pipefail

# Read JSON from stdin
if [ -t 0 ]; then INPUT="{}"; else INPUT=$(cat); fi

TOOL_NAME=""
FILE_PATH=""

# Parse with jq if available
if command -v jq >/dev/null 2>&1; then
  TOOL_NAME=$(printf '%s' "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null || true)
  FILE_PATH=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)
else
  # Fallback: crude grep-based extraction
  TOOL_NAME=$(printf '%s' "$INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/' || true)
  FILE_PATH=$(printf '%s' "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/' || true)
fi

# Only trigger on Write or Edit
if [ "$TOOL_NAME" != "Write" ] && [ "$TOOL_NAME" != "Edit" ]; then
  exit 0
fi

[ -z "$FILE_PATH" ] && exit 0

# Design document path patterns, including the default /spec output.
DESIGN_PATTERNS="(^|/)SPEC\\.md$|docs/ideas/|design/|Idea/|ProjectDoc/|\\.spec\\.md|design-.*\\.md|architecture.*\\.md"

IS_DESIGN_DOC=0
if echo "$FILE_PATH" | grep -qE "$DESIGN_PATTERNS"; then
  IS_DESIGN_DOC=1
fi

# Also check if the file content looks like a design doc (contains design-related sections)
if [ "$IS_DESIGN_DOC" -eq 0 ] && [ -f "$FILE_PATH" ]; then
  if head -50 "$FILE_PATH" 2>/dev/null | grep -qE '^#+[[:space:]]+(Design|Architecture|Spec|Specification|提案|设计|架构|方案)(:|[[:space:]])'; then
    IS_DESIGN_DOC=1
  fi
fi

if [ "$IS_DESIGN_DOC" -eq 1 ]; then
  # Extract a friendly filename for the message
  DISPLAY_NAME=$(basename "$FILE_PATH")

  if command -v jq >/dev/null 2>&1; then
    jq -cn \
      --arg file "$DISPLAY_NAME" \
      --arg path "$FILE_PATH" \
      '{priority: "ADVISORY", message: ("\n💡 你刚刚写入了设计文档: \($file)\n   建议运行 /grill-me 对其进行压力测试，发现隐含假设和潜在风险后再进入实现阶段。\n   Usage: /grill-me \($path)\n")}'
  else
    printf '{"priority":"ADVISORY","message":"\n💡 你刚刚写入了设计文档: %s\n   建议运行 /grill-me 对其进行压力测试，发现隐含假设和潜在风险后再进入实现阶段。\n   Usage: /grill-me %s\n"}\n' "$DISPLAY_NAME" "$FILE_PATH"
  fi
fi

exit 0
