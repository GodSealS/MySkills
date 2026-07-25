#!/bin/bash
# agent-skills session start hook for CodeBuddy
# Injects the cs-using meta-skill into every new session

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$(dirname "$SCRIPT_DIR")/skills"
META_SKILL="$SKILLS_DIR/cs-using/SKILL.md"

if ! command -v jq >/dev/null 2>&1; then
  echo '{"priority": "INFO", "message": "agent-skills: jq is required for the session-start hook but was not found on PATH. Install jq to enable meta-skill injection. Skills remain available individually."}'
  exit 0
fi

if [ -f "$META_SKILL" ]; then
  CONTENT=$(cat "$META_SKILL")
  jq -cn \
    --arg message "agent-skills loaded. Use the skill discovery flowchart to find the right skill for your task.

$CONTENT" \
    '{priority: "IMPORTANT", message: $message}'
else
  echo '{"priority": "INFO", "message": "agent-skills: cs-using meta-skill not found. Skills may still be available individually."}'
fi
