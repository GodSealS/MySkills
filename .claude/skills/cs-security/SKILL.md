---
name: cs-security
model: opus
description: "Hardens code against vulnerabilities. Use when handling user input, authentication, data storage, or external integrations. Use when building any feature that accepts untrusted data, manages user sessions, or interacts with third-party services. / 安全加固代码。用于处理用户输入、认证、数据存储或外部集成——任何接受不可信数据、管理用户会话或与第三方服务交互的功能。"
---

# Security and Hardening

## Overview

Security-first development practices for web applications. Treat every external input as hostile, every secret as sacred, and every authorization check as mandatory. Security isn't a phase — it's a constraint on every line of code that touches user data, authentication, or external systems.

## When to Use

- Building anything that accepts user input
- Implementing authentication or authorization
- Storing or transmitting sensitive data
- Integrating with external APIs or services
- Adding file uploads, webhooks, or callbacks
- Handling payment or PII data

**Owner Routing:** Security remediation stays with the affected slice. FAN-OUT to `cs-backend-lead` for server trust boundaries, authentication, data access, and external integrations; FAN-OUT to `cs-frontend-lead` for browser input handling, rendering, and client storage. `cs-security-auditor` independently reviews the result and does not implement the feature.

## Process: Threat Model First

1. **Map the trust boundaries.** Where does untrusted data enter your system?
2. **Name the assets.** What's worth stealing or breaking?
3. **Run STRIDE over each boundary:** Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege
4. **Write abuse cases next to use cases.**

## The Three-Tier Boundary System

### Always Do (No Exceptions)
- Validate all external input at system boundaries
- Parameterize all database queries
- Encode output to prevent XSS
- Use HTTPS for all external communication
- Hash passwords with bcrypt/scrypt/argon2
- Set security headers (CSP, HSTS, X-Frame-Options)
- Use httpOnly, secure, sameSite cookies for sessions
- Run `npm audit` before every release

### Ask First (Requires Human Approval)
- Adding new authentication flows
- Storing new categories of sensitive data
- Adding new external service integrations
- Changing CORS configuration
- Adding file upload handlers

### Never Do
- Never commit secrets to version control
- Never log sensitive data (passwords, tokens)
- Never trust client-side validation as a security boundary
- Never use `eval()` or `innerHTML` with user-provided data
- Never expose stack traces to users

## OWASP Top 10 Prevention

### Injection (SQL, NoSQL, OS Command)
Use parameterized queries. Never concatenate user input into SQL.

### Broken Authentication
Hash passwords with bcrypt (12 rounds minimum). Use secure session management.

### Sensitive Data Exposure
Secrets in environment variables. Encrypt data in transit and at rest.

## AI / LLM Security (if applicable)
- Never pass model output to `eval`, SQL, shell, `innerHTML`
- Never rely on system prompts as a security boundary
- Scope tool/agent permissions tightly
- Set token, rate, and recursion limits

## Severity Classification

| Severity | Criteria | Action |
|----------|----------|--------|
| **Critical** | Exploitable remotely, data breach possible | Fix immediately |
| **High** | Exploitable with conditions, significant exposure | Fix before release |
| **Medium** | Limited impact or requires auth | Fix in current sprint |
| **Low** | Theoretical risk or defense-in-depth | Schedule next sprint |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's just internal tooling" | Internal tools are often less audited, making them valuable attack vectors. |
| "The framework handles security" | Frameworks provide defaults, not guarantees. Verify. |
| "We'll do a security review later" | Security reviews happening after merge find things that are expensive to fix. |

## Verification

- [ ] No secrets in code or version control
- [ ] `npm audit` shows no critical/high vulnerabilities
- [ ] Input validation on all user-facing endpoints
- [ ] All database queries are parameterized
- [ ] Security headers configured
- [ ] Error messages are generic (no stack traces to users)
- [ ] Dependencies audited for known CVEs

## See Also

- `../../references/cs-security-checklist.md`
