# Security Policy — MemPolygraph

## What never gets committed here
- K3 memory engine source code and the agent's internal prompts (private)
- API keys, tokens, private keys, `.env` files, `*registration.json`, `*.db`
- Raw agent memories — only SHA-256 fingerprints and aggregate counts

## Reporting
Open a GitHub issue titled `[security]` (no PoC details) or contact the maintainer.
Fixes are coordinated privately before any public disclosure.
