FROM python:3.12-slim
WORKDIR /app
COPY src/ ./src/
COPY fixtures/ ./fixtures/
COPY scripts/ ./scripts/
RUN python -m src.eval_harness --memories fixtures/synthetic_memories.json \
    --eval fixtures/eval_set.json --out evidence_last_run.json \
 && python -m src.passport_generator --results evidence_last_run.json \
    --out evidence_passport.json --agent demo-agent \
 && rm evidence_last_run.json
CMD ["cat", "evidence_passport.json"]
