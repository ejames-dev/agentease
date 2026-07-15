# Security Policy

## Supported Versions

AgentEase is pre-1.0 software. Security fixes are applied to the latest released
minor version; older minor versions may not receive fixes. The unreleased 0.2.0
code is under active development and should not be treated as a supported
production release.

## Reporting a Vulnerability

Please do not disclose a suspected vulnerability in a public issue, discussion,
or pull request.

Use the repository's
[private vulnerability-reporting form](https://github.com/ejames-dev/agentease/security/advisories/new).
If GitHub's private reporting service is unavailable, email the maintainer at
`newmanevan@myyahoo.com` with:

- the affected version and configuration
- a minimal reproduction or proof of concept
- the security impact you observed
- any suggested remediation or disclosure constraints

Do not include real customer data, credentials, API keys, or other secrets in a
report. You may use synthetic test data and redacted logs.

The maintainer will acknowledge the report, investigate it, and coordinate
disclosure and a fix as circumstances allow. No fixed response or remediation
time is promised by this community project.

## Security Boundaries in 0.2.0

AgentEase replaces covered values in process before constructing a provider
prompt. It does not provide comprehensive de-identification or a hardened
security boundary.

The built-in scrubber recognizes a limited set of regex forms: ASCII-style
email addresses, North American 10-digit phone numbers with optional country
code and separators, 13-19 digit Luhn-valid card numbers, and hyphenated
`NNN-NN-NNNN` SSN-like values. It can miss sensitive data and can match benign
data. Names, addresses, dates of birth, general international phone numbers,
secrets, and many regulated identifiers are not built in. See the exact table in
[README.md](README.md#pii-scrubber-exact-built-in-coverage).

Additional boundaries:

- A live run sends the sanitized prompt to the configured LLM provider.
- An unmatched sensitive value is sent as part of that prompt.
- A repair attempt is another provider call containing the sanitized context,
  invalid model response, and required schema.
- The default metrics recorder is in-memory and local-only. It records metadata,
  not the original input or the captured PII values.
- Offline mode is deterministic local fixture logic, not a local LLM and not a
  production security control.
- Workflow results and recommended actions are advisory. AgentEase does not
  enforce access, retention, routing, sales, support, or compliance policy.
- Document classification accepts caller-supplied plain text only; it does not
  safely parse, scan, or sanitize PDF, DOCX, image, or email-container files.
- The 0.2.0 release has no hosted dashboard, RAG layer, Node.js SDK,
  Presidio-backed detection, or remote AgentEase telemetry.

## Deployment Guidance

Before production use:

1. Test the scrubber against your actual data formats and add narrow custom
   patterns where appropriate.
2. Treat provider credentials as secrets and grant them the minimum necessary
   privileges.
3. Review the configured provider's data retention, training, residency, and
   subprocessors.
4. Validate the exact model/provider combination; only the OpenAI path is
   release-certified for 0.2.0, while other LiteLLM providers are best effort.
5. Keep human review around high-impact classifications and actions.
6. Apply normal dependency scanning, logging controls, egress controls, and
   secret-management practices in the host application.

Security claims should describe what AgentEase actually masks and validates,
not imply that regex substitution guarantees privacy or regulatory compliance.
