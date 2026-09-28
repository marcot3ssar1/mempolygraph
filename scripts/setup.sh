#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m src.eval_harness --memories fixtures/synthetic_memories.json --eval fixtures/eval_set.json --out evidence/last_run.json
python -m src.passport_generator --results evidence/last_run.json --out evidence/example_passport.json --agent demo-agent
echo "passport ready: evidence/example_passport.json"
