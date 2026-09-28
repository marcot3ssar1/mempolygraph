"""MemPolygraph eval harness — recall@k, abstention, adversarial negatives.

Usage:
    python -m src.eval_harness --memories fixtures/synthetic_memories.json \
        --eval fixtures/eval_set.json --out evidence/last_run.json
Exit 0 on gate PASS, 1 on FAIL. Deterministic: double run must match.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time

sys.path.insert(0, ".")
from src.generic_exporter import FileStore

GATE = {"recall_at_3": 0.50, "abstain_acc": 0.50, "adv_clean": 0.50}


def run_eval(store, questions, top_k=3):
    rec_hit = rec_tot = abs_ok = abs_tot = adv_ok = adv_tot = 0
    rows = []
    for item in questions:
        t0 = time.monotonic()
        hits = store.query(item["q"], top_k=top_k)
        dt_ms = (time.monotonic() - t0) * 1000
        kind = item["kind"]
        if kind == "recall":
            rec_tot += 1
            ok = any(h.id == item["answer_id"] for h in hits)
            rec_hit += ok
        elif kind == "unanswerable":
            abs_tot += 1
            ok = len(hits) == 0
            abs_ok += ok
        else:  # adversarial: must NOT return a confident hit for the trap
            adv_tot += 1
            ok = not any(h.score >= 0.8 for h in hits)
            adv_ok += ok
        rows.append({"q": item["q"][:60], "kind": kind, "ok": ok,
                     "ms": round(dt_ms, 1)})
    return {
        "recall_at_3": rec_hit / max(1, rec_tot),
        "abstain_acc": abs_ok / max(1, abs_tot),
        "adv_clean": adv_ok / max(1, adv_tot),
        "n_recall": rec_tot, "n_abstain": abs_tot, "n_adv": adv_tot,
        "rows": rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--memories", required=True)
    ap.add_argument("--eval", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    store = FileStore(a.memories)
    with open(a.eval, encoding="utf-8") as f:
        questions = json.load(f)["questions"]

    r1 = run_eval(store, questions)
    r2 = run_eval(store, questions)  # determinism check
    blob = json.dumps({k: r1[k] for k in ("recall_at_3", "abstain_acc", "adv_clean")}, sort_keys=True)
    deterministic = blob == json.dumps({k: r2[k] for k in ("recall_at_3", "abstain_acc", "adv_clean")}, sort_keys=True)

    passed = (r1["recall_at_3"] >= GATE["recall_at_3"]
              and r1["abstain_acc"] >= GATE["abstain_acc"]
              and r1["adv_clean"] >= GATE["adv_clean"]
              and deterministic)
    report = {"store": store.describe(), "gate": GATE,
              "metrics": r1, "deterministic": deterministic,
              "pass": passed}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps({"pass": passed, "metrics": {k: r1[k] for k in ("recall_at_3", "abstain_acc", "adv_clean")},
                      "deterministic": deterministic}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
