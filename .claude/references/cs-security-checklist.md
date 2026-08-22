# Security Checklist

> Ported from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT)

## Pre-Commit Security Checks

- [ ] No secrets in code (API keys, passwords, tokens)
- [ ] No secrets in configuration files
- [ ] `.env` files in `.gitignore`
- [ ] `npm audit` passes with no critical/high vulnerabilities

## Authentication & Authorization

- [ ] Passwords hashed with bcrypt/scrypt/argon2 (min 12 rounds)
- [ ] Sessions use httpOnly, secure, sameSite cookies
- [ ] Authorization checked on every protected endpoint
- [ ] Rate limiting on auth endpoints
- [ ] Password reset tokens time-limited and single-use

## Input Validation

- [ ] All user input validated at system boundaries
- [ ] SQL queries parameterized (no string concatenation)
- [ ] HTML output encoded to prevent XSS
- [ ] File uploads restricted by type, size, content
- [ ] URL redirects validated against allowlist

## Infrastructure

- [ ] Security headers configured (CSP, HSTS, X-Frame-Options)
- [ ] CORS restricted to specific origins
- [ ] HTTPS enabled for all external communication
- [ ] Error messages generic (no stack traces to users)

## AI / LLM Security

- [ ] Model output treated as untrusted (never passed to eval/shell/SQL)
- [ ] System prompts not relied on as security boundary
- [ ] Tool/agent permissions scoped with confirmation for destructive actions

## See Also

- `cs-security` skill for full hardening workflow
- `cs-security-auditor` agent for security audits
