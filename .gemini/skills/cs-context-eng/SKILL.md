---
name: cs-context-eng
description: "Optimizes agent context setup. Use when starting a new session, when agent output quality degrades, when switching between tasks, or when you need to configure rules files and context for a project. / 优化Agent上下文设置。用于启动新会话、Agent输出质量下降时、任务切换时、或配置项目规则文件和上下文时。"
---

# Context Engineering

## Overview

Feed agents the right information at the right time. Context is the single biggest lever for agent output quality — too little and the agent hallucinates, too much and it loses focus. Context engineering is the practice of deliberately curating what the agent sees, when it sees it, and how it's structured.

## When to Use

- Starting a new coding session
- Agent output quality is declining (wrong patterns, hallucinated APIs)
- Switching between different parts of a codebase
- Setting up a new project for AI-assisted development
- The agent is not following project conventions

## The Context Hierarchy

```
1. Rules Files (CODEBUDDY.md, AGENTS.md)   ← Always loaded, project-wide
2. Spec / Architecture Docs              ← Loaded per feature/session
3. Relevant Source Files                 ← Loaded per task
4. Conversation History                  ← Current session
```

## Progressive Disclosure

Load context in layers — only what's needed for the current task:
1. Start minimal: rules + spec summary
2. Add source files as the task narrows
3. Add test files when implementing
4. Add documentation when making architectural decisions

## Context Packing

When the context window is full:
1. Summarize earlier conversation stages
2. Keep recent turns in full detail
3. Preserve key decisions and rationales
4. Drop verbose code that's been summarized

## Rules Files Best Practices

- Keep rules under 500 lines
- Front-load the most important conventions
- Use progressive disclosure (link to detailed docs rather than inlining)
- Update rules when conventions change

## MCP Integrations

MCP servers extend context by giving agents access to:
- Real-time documentation (WebFetch)
- Runtime data (DevTools, Database tools)
- Project knowledge graphs

Configure MCP servers in `.codebuddy/settings.json`.

## Verification

- [ ] Agent consistently follows project conventions
- [ ] Output quality doesn't degrade within a session
- [ ] Rules files are up to date
- [ ] Context is appropriately scoped — not too little, not too much
