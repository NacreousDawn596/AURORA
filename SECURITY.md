# Security Policy

AURORA may execute source code from repositories; treat that code as untrusted input.

## Reporting

Do not open a public issue containing credentials, exploit details against real systems or sensitive execution artifacts. Use GitHub's private vulnerability reporting feature where available.

## Security principles

- Run untrusted build/test workloads in isolated, unprivileged containers.
- Apply CPU, memory, process and time limits.
- Disable network access by default.
- Do not mount the host container socket into untrusted workloads.
- Do not expose production credentials to build/test workers.
- Use short-lived, least-privilege credentials.
- Pin and record action versions and image digests.
- Treat logs and test output as untrusted content.
- Keep LLM tools behind a typed policy gateway.
- Require explicit policy authorization for deployment and rollback.

## Current status

The initial repository is a small Python prototype. These controls are design requirements, not a claim that the complete execution platform is implemented.
