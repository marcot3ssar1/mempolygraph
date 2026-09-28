# MemPolygraph — verifiable memory-quality passports for AI agents

> Keycard certifies *who* an agent is. MemPolygraph certifies *whether its memory tells the truth* — with reproducible proof.
> Built for Colosseum Crypto World's Fair (Solana track).

## What it does
Point MemPolygraph at any agent memory store through a tiny black-box interface.
It runs a fixed eval battery — recall, abstention on unanswerables, adversarial negatives —
and issues a signed-style passport: score breakdown + SHA-256 fingerprint. No engine source needed, ever.

## Quick start
```bash
./scripts/setup.sh
python -m src.eval_harness --fixtures fixtures/synthetic_memories.json --eval fixtures/eval_set.json
python -m src.passport_generator --results evidence/last_run.json --out evidence/example_passport.json
```

## Track record (linked, not copied)
- [`k3-trust-validation`](https://github.com/marcot3ssar1/k3-trust-validation) — eval harness pattern + methodology that scored 71.87 → 90.0 Elder on a live registry
- [`synapse-evidence`](https://github.com/marcot3ssar1/synapse-evidence) — capability docs + redacted evidence

## Security
See [SECURITY.md](SECURITY.md). In short: no engine internals, prompts, keys, tokens, or raw memories are ever committed here.
