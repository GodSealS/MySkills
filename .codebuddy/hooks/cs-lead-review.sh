#!/bin/bash
# cs-lead-review.sh — PostToolUse hook for Write|Edit (CodeBuddy)
# Detects frontend/backend/architecture file writes and suggests the owning domain lead.
# This hook is advisory only; the skill workflow performs any actual fan-out.
# Dependencies: jq.

set -euo pipefail

# Read JSON from stdin
if [ -t 0 ]; then INPUT="{}"; else INPUT=$(cat); fi

TOOL_NAME=""
FILE_PATH=""

command -v jq >/dev/null 2>&1 || exit 0
TOOL_NAME=$(printf '%s' "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null || true)
FILE_PATH=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null || true)

# Only trigger on Write or Edit
if [ "$TOOL_NAME" != "Write" ] && [ "$TOOL_NAME" != "Edit" ]; then
  exit 0
fi

[ -z "$FILE_PATH" ] && exit 0

# Map file path to owning domain lead.
# Resolution order:
#   1) directory keyword (most reliable)
#   2) unambiguous extension (.go/.py → backend, .tsx/.vue → frontend)
#   3) content heuristic for ambiguous extensions (.ts/.js) as a fallback
LEAD_NAME=""
LEAD_HINT=""

# 1) Directory keyword
if echo "$FILE_PATH" | grep -qiE '(^|/)(architecture|arch|design|docs/adr)/|\.adr\.md$'; then
  LEAD_NAME="cs-architect"
  LEAD_HINT="架构设计/ADR 文件，建议 fan-out cs-architect 校验模块边界与依赖方向"
elif echo "$FILE_PATH" | grep -qiE '(^|/)(server|backend|api|apis|service|services|infra|db|database|migrations?|model|models|module|modules|entity|entities|dto|repository|repositories|controller|controllers|handler|handlers|route|routes|router|routers|middleware|middlewares)/'; then
  LEAD_NAME="cs-backend-lead"
  LEAD_HINT="后端切片，建议 fan-out cs-backend-lead（contract-first，服务端安全与性能）"
elif echo "$FILE_PATH" | grep -qiE '(^|/)(client|frontend|web|ui|components?|pages?|views?|hooks?|styles?|layouts?)/'; then
  LEAD_NAME="cs-frontend-lead"
  LEAD_HINT="前端切片，建议 fan-out cs-frontend-lead（生产级 UI + 浏览器验证）"
fi

# 2) Unambiguous extension (only when directory didn't decide)
if [ -z "$LEAD_NAME" ]; then
  if echo "$FILE_PATH" | grep -qiE '\.(go|rs|py|java|kt|rb|php|sql)$'; then
    LEAD_NAME="cs-backend-lead"
    LEAD_HINT="后端文件（语言后缀），建议 fan-out cs-backend-lead"
  elif echo "$FILE_PATH" | grep -qiE '\.(jsx|tsx|vue|svelte|css|scss|less|html?)$'; then
    LEAD_NAME="cs-frontend-lead"
    LEAD_HINT="前端文件（语言后缀），建议 fan-out cs-frontend-lead（生产级 UI + 浏览器验证）"
  fi
fi

# 3) Content heuristic for ambiguous extensions (.ts/.js/.mjs/.cjs)
if [ -z "$LEAD_NAME" ] && [ -f "$FILE_PATH" ]; then
  case "${FILE_PATH##*.}" in
    ts|js|mjs|cjs)
      HEAD=$(head -80 "$FILE_PATH" 2>/dev/null || true)
      if [ -n "$HEAD" ]; then
        # Frontend signal, unless a strong backend signal coexists
        if printf '%s' "$HEAD" | grep -qE 'import React|from .react|useState|useEffect|useRef|className=|styled\.|styled\(|createElement'; then
          if ! printf '%s' "$HEAD" | grep -qE 'express|mongoose|prisma|sequelize|typeorm|node:http|node:fs|from .fs|router\.(get|post)|app\.(get|post)|pool\.query|connection\.query|SELECT |CREATE TABLE|INSERT INTO|require\(.http'; then
            LEAD_NAME="cs-frontend-lead"
            LEAD_HINT="前端文件（内容启发），建议 fan-out cs-frontend-lead（生产级 UI + 浏览器验证）"
          fi
        fi
        # Backend signal
        if [ -z "$LEAD_NAME" ]; then
          if printf '%s' "$HEAD" | grep -qE 'express|mongoose|prisma|sequelize|typeorm|node:http|node:fs|from .fs|router\.(get|post)|app\.(get|post)|pool\.query|connection\.query|SELECT |CREATE TABLE|INSERT INTO|require\(.http'; then
            LEAD_NAME="cs-backend-lead"
            LEAD_HINT="后端文件（内容启发），建议 fan-out cs-backend-lead（contract-first，服务端安全与性能）"
          fi
        fi
      fi
      ;;
  esac
fi

if [ -n "$LEAD_NAME" ]; then
  DISPLAY_NAME=$(basename "$FILE_PATH")

  jq -cn \
    --arg file "$DISPLAY_NAME" \
    --arg lead "$LEAD_NAME" \
    --arg hint "$LEAD_HINT" \
    '{priority: "ADVISORY", message: ("\n💡 你刚刚写入了领域文件: \($file)\n   \($hint)\n   请由当前 skill 按 owner 路由执行 \($lead) 的 fan-out。\n")}'
fi

exit 0
