# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.4.x   | :white_check_mark: |
| < 0.4   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within FDMM, please send an email to **[INSERT EMAIL]**. All security vulnerabilities will be promptly addressed.

**Please do not report security vulnerabilities through public GitHub issues.**

### What to Include

When reporting a vulnerability, please include:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if any)

### Response Expectations

- **Acknowledgement**: Within 48 hours of your report
- **Assessment**: Within 1 week, we will assess the severity and validity
- **Fix**: Critical vulnerabilities will be patched as soon as possible
- **Disclosure**: We will coordinate with you on the timing of public disclosure

## Disclosure Policy

We follow coordinated disclosure:

1. **Report received** — We acknowledge receipt within 48 hours
2. **Investigation** — We investigate and confirm the vulnerability
3. **Fix developed** — We develop and test a fix
4. **Release** — We release the fix in a patch version
5. **Disclosure** — We publish a security advisory after the fix is available

We ask that you give us reasonable time to address the issue before public disclosure.

## Security Best Practices

When using FDMM in production:

- Keep Python and dependencies up to date
- Run with the minimum required privileges
- Monitor for unexpected behaviour in matching operations
- Validate all input data before passing to the algorithm

## Scope

This security policy applies to:

- The `maxmatch` Python package
- The source code in this repository
- CI/CD workflows

It does **not** apply to:

- Third-party dependencies (report to their maintainers)
- Issues in the original paper's algorithm design
