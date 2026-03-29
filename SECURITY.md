# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| 0.2.x | Yes |
| 0.1.x | No |

## Reporting a vulnerability

Please do **not** open a public GitHub issue for a suspected vulnerability.

Instead, privately contact the maintainers and include:

- affected version
- reproduction steps
- impact assessment
- whether a public disclosure deadline applies

A good report should let maintainers reproduce the issue quickly.

## Response target

Initial triage target: within 5 business days.

## Scope examples

Relevant reports include:

- parser bypasses that accept malformed or ambiguous FSMs
- validation gaps that permit illegal workflow graphs
- runtime bypasses that allow out-of-order execution
- release automation weaknesses that could compromise published artifacts
