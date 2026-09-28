# Methodology — how a MemPolygraph passport is issued

## Threat model
We assume the memory store is untrusted: it may invent content (hallucination),
stay silent when it should answer, or be tuned to pass naive evals. The passport
must be reproducible by a third party running only this repo + public fixtures.

## Battery (12 questions, 3 kinds)
- **recall (8)**: answer must be the exact memory id in top-3. Measures retrieval quality.
- **unanswerable (2)**: correct behavior is zero hits. A store that always answers
  is penalized — this is the anti-invention gate.
- **adversarial (2)**: trap statements mixing true fragments with false claims.
  Any hit with score >= 0.8 counts as a confident false recall → fail.

## Gates (v0.1, MockStore baseline)
`recall@3 >= 0.50`, `abstain_acc >= 0.50`, `adv_clean >= 0.50`, plus a
double-run determinism check. Current: 0.875 / 1.0 / 1.0, deterministic.

## Scoring
`accuracy = 0.6*recall + 0.2*abstain + 0.2*adv_clean`.
Fingerprint = SHA-256 over the scored document minus `fingerprint`/`issued_at`,
so anyone can recompute it (see `verify` field in the passport).

## What the passport does NOT prove
- It certifies the *retrieval behavior* observed during the eval window, not future behavior.
- It says nothing about the engine internals — the store stays black-box by design.
- Fixture scores are a smoke test; production passports must use held-out eval sets.

## Track record of this method on a live registry
Same pattern (export → eval → score → falsifiable prediction deltas) moved a live
agent passport 71.87 → 90.0 Elder. Links in README.
