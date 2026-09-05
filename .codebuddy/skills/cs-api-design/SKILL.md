---
name: cs-api-design
description: "Guides stable API and interface design. Use when designing APIs, module boundaries, or any public interface. Use when creating REST or GraphQL endpoints, defining type contracts between modules, or establishing boundaries between frontend and backend. / 指导稳定的API和接口设计。用于设计API、模块边界或任何公共接口——REST/GraphQL端点、模块间类型契约、前后端边界定义。"
argument-hint: "[API or interface to design]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task
agent: cs-code-reviewer
---

# API and Interface Design

## Overview

Design stable, well-documented interfaces that are hard to misuse. Good interfaces make the right thing easy and the wrong thing hard. This applies to REST APIs, GraphQL schemas, module boundaries, component props, and any surface where one piece of code talks to another.

**Domain Owner:** When this skill is used to design or implement a backend-owned slice (primary owner: `backend` in the task plan), **FAN-OUT to `cs-backend-lead`** (via `Task`). The lead owns the interface and its implementation; this skill provides the design standards. The contract this skill produces is the handshake with `cs-frontend-lead` — define it explicitly before implementation.

## When to Use

- Designing new API endpoints
- Defining module boundaries or contracts between teams
- Creating component prop interfaces
- Establishing database schema that informs API shape
- Changing existing public interfaces

## Core Principles

### Hyrum's Law
With a sufficient number of users, all observable behaviors will be depended on by somebody — regardless of what you promise in the contract. Be intentional about what you expose.

### The One-Version Rule
API changes should have exactly one version in production at a time. Multiple API versions compound maintenance costs.

### Contract-First Design
Define the interface before implementing it. This means:
1. Write the contract (OpenAPI spec, TypeScript types, GraphQL schema)
2. Get agreement from consumers
3. Then implement

## Error Semantics

- Use consistent error shapes across the API
- Return appropriate HTTP status codes
- Include actionable error messages
- Never expose internal stack traces

```typescript
// Good error shape
interface ApiError {
  error: {
    code: string;      // Machine-readable: "VALIDATION_ERROR"
    message: string;   // Human-readable: "Title is required"
    details?: unknown; // Optional field-level errors
  };
}
```

## Boundary Validation

Validate at every trust boundary:
- HTTP request → validate in middleware/route handler
- Database write → validate schema constraints
- External API response → validate before using
- User input → validate + sanitize

## Versioning Strategy

- Prefer backward-compatible changes
- When breaking changes are needed, version the API (v1, v2)
- Deprecate old versions with clear timelines
- See `cs-deprecation` for safe deprecation patterns

## Common Anti-patterns

- Exposing internal implementation details in API shapes
- Returning raw database rows instead of shaped DTOs
- Inconsistent error formats between endpoints
- Using GET for state-changing operations
- Breaking changes without versioning

## Verification

- [ ] API contract is defined before implementation
- [ ] Error responses use consistent format
- [ ] All trust boundaries have validation
- [ ] Breaking changes are versioned or avoided
- [ ] Documentation matches implementation

## Orchestration

- **Backend slice design/implementation** → FAN-OUT to `cs-backend-lead`
- **Frontend consumer** → `cs-frontend-lead`; the contract must be explicit and versioned before frontend consumes it
- **Architecture boundaries** → set by `cs-architect`; surface disagreements in the report, do not silently redesign
- **Breaking changes** → route through `cs-deprecation`
- **Tests** → follow `cs-tdd` for backend logic; Prove-It pattern for bugs
