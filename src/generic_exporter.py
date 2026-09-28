"""MemPolygraph generic exporter — black-box memory-store interface.

Any memory system plugs in by implementing MemoryStore.query().
Bundled: MockStore (deterministic, for CI/judges) and FileStore (JSON file).
The private K3 engine is wrapped OUT OF TREE by K3Adapter (never committed).
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class MemoryHit:
    id: str
    content: str
    citations: list = field(default_factory=list)
    score: float = 0.0


class MemoryStore(ABC):
    name: str = "base"

    @abstractmethod
    def query(self, text: str, top_k: int = 5):
        """Return list[MemoryHit] most relevant to text. Empty list = abstain signal."""

    def describe(self):
        return {"name": self.name, "kind": self.__class__.__name__}


class MockStore(MemoryStore):
    """Deterministic store over an in-memory list. Powers fixtures + CI."""

    name = "mock"

    def __init__(self, memories):
        self._mems = [
            {"id": m["id"], "content": m["content"],
             "citations": m.get("citations", []),
             "tokens": set(m["content"].lower().split())}
            for m in memories
        ]

    def query(self, text: str, top_k: int = 5, min_score: float = 0.25):
        if len(text.split()) < 2:
            return []  # gate: degenerate query -> abstain
        qtok = set(text.lower().split())
        ranked = sorted(
            self._mems,
            key=lambda m: len(qtok & m["tokens"]) / max(1, len(qtok | m["tokens"])),
            reverse=True,
        )
        out = []
        for m in ranked[:top_k]:
            overlap = len(qtok & m["tokens"])
            if overlap == 0:
                continue
            score = overlap / max(1, len(qtok))
            if score < min_score:
                continue  # abstention gate: weak overlap -> no answer
            out.append(MemoryHit(id=m["id"], content=m["content"],
                                 citations=m["citations"], score=score))
        return out


class FileStore(MockStore):
    """MockStore loaded from a JSON file: {"memories": [{id, content, citations}]}."""

    name = "file"

    def __init__(self, path: str):
        with open(path, encoding="utf-8") as f:
            super().__init__(json.load(f)["memories"])
        self.name = f"file:{path}"
