# Security Policy

## Educational use only

**This project is not a security system.**

Biometric Workshop Suite is an educational demonstration tool. Its algorithms, data storage, and architecture are intentionally simplified for teaching purposes. It provides **no meaningful security guarantees** and must never be used to protect real systems, data, or identities.

Specifically:

- Biometric templates are stored as plain JSON with no encryption
- The admin PIN is a lightweight teaching aid, not a hardened authentication mechanism
- Matching algorithms are designed to be transparent and observable, not resistant to attack
- No rate limiting, brute-force protection, or audit logging is implemented
- The Flask secret key defaults to a static development value

These are **not bugs** — they are deliberate design choices to keep the codebase readable and the concepts accessible to students.

---

## Reporting a vulnerability

If you find a vulnerability that could put users of this project at risk (for example, a server-side code execution issue or a dependency with a known CVE), please report it responsibly:

1. **Do not open a public GitHub issue.**
2. Email the maintainer directly, or use [GitHub's private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) if enabled on this repository.
3. Include a description of the issue, steps to reproduce, and any suggested remediation.

We will acknowledge the report within 7 days and aim to release a fix or mitigation within 30 days for issues that genuinely affect users running the tool in a workshop setting.

---

## Scope

The following are **out of scope** as vulnerabilities, given the educational context of this project:

- The admin PIN being stored in plaintext
- Biometric templates being readable in JSON files
- Absence of HTTPS enforcement
- Absence of CSRF protection on API endpoints
- The static (docs/) version having no server-side validation

If you are unsure whether your finding is in scope, please report it privately and we will respond.
