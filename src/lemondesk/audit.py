"""Append-only JSONL audit log for every model call (real or demo)."""
from __future__ import annotations
import hashlib, json, os, time
from datetime import datetime, timezone

def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

class AuditLog:
    def __init__(self, path: str):
        self.path = path
    def record(self, *, task: str, model: str, mode: str, prompt: str, latency_ms: float) -> dict:
        if mode not in ("real", "demo"):
            raise ValueError("mode must be 'real' or 'demo'")
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task": task, "model": model, "mode": mode,
            "prompt_hash": prompt_hash(prompt),
            "prompt_chars": len(prompt),
            "latency_ms": round(float(latency_ms), 3),
        }
        d = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(d, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry
    def read_all(self) -> list:
        if not os.path.exists(self.path):
            return []
        with open(self.path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
