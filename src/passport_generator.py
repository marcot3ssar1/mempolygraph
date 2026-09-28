"""MemPolygraph passport generator — metrics + SHA-256 fingerprint, no raw content.

Usage:
    python -m src.passport_generator --results evidence/last_run.json --out evidence/example_passport.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--agent", default="demo-agent")
    a = ap.parse_args()

    with open(a.results, encoding="utf-8") as f:
        run = json.load(f)
    m = run["metrics"]
    accuracy = round((m["recall_at_3"] * 0.6 + m["abstain_acc"] * 0.2 + m["adv_clean"] * 0.2), 4)
    scored = {"agent": a.agent,
              "scores": {"accuracy": accuracy, "recall_at_3": m["recall_at_3"],
                         "abstain_acc": m["abstain_acc"], "adv_clean": m["adv_clean"]},
              "gate": run["gate"], "gate_pass": run["pass"],
              "deterministic": run["deterministic"],
              "n_eval": m["n_recall"] + m["n_abstain"] + m["n_adv"]}
    fp = hashlib.sha256(json.dumps(scored, sort_keys=True).encode()).hexdigest()
    passport = {**scored,
                "issued_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "fingerprint": fp,
                "verify": "sha256 over this document minus fingerprint and issued_at fields"}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(passport, f, indent=2)
    print(json.dumps({"agent": a.agent, "accuracy": accuracy,
                      "fingerprint": fp[:16] + "...", "gate_pass": run["pass"]}, indent=2))


if __name__ == "__main__":
    sys.exit(main())
