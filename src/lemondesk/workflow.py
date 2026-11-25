"""Core workflow: document -> summary + KO<->EN translation + action items.
Lemonade is INSIDE the reasoning loop: when a server is reachable, every task
(summary, translation, action extraction) is a separate Lemonade chat completion,
each one audit-logged. The model never exports anything: export is deterministic
code behind a human ApprovalGate (structural, not a prompt instruction).
Boundary declaration: "The model never decides what gets exported. Only action
items whose IDs a human explicitly approved are exported; 0 approvals = 0 exported."
"""
from __future__ import annotations
import json, time
from .audit import AuditLog
from .client import LemonadeClient, LemonadeUnavailable
from . import demo

PROMPTS = {
    "summarize": "Summarize the following document in 3 sentences or fewer, in its original language.\n\n{document}",
    "translate": "Translate the following document into {target_name}. Output only the translation.\n\n{document}",
    "actions": "Extract action items from the following document. Output one action item per line, no numbering, no commentary. If there are none, output nothing.\n\n{document}",
}

class ApprovalGate:
    """Structural human-approval gate. Export is impossible without approvals."""
    def __init__(self, items: list):
        self.items = items
        self.approved: set = set()
    def approve(self, item_id: str) -> None:
        if item_id not in {i["id"] for i in self.items}:
            raise KeyError(f"unknown action item id: {item_id}")
        self.approved.add(item_id)
    def export(self) -> list:
        """Returns ONLY approved items. With zero approvals this returns []."""
        return [i for i in self.items if i["id"] in self.approved]
    def export_json(self) -> str:
        return json.dumps(self.export(), ensure_ascii=False, indent=2)

def _run_task(task, prompt, client, audit, fallback):
    start = time.perf_counter()
    if client is not None:
        try:
            text, model = client.chat([{"role": "user", "content": prompt}])
            latency = (time.perf_counter() - start) * 1000
            if audit: audit.record(task=task, model=model, mode="real", prompt=prompt, latency_ms=latency)
            return text.strip(), "real", model
        except LemonadeUnavailable:
            pass
    result = fallback()
    latency = (time.perf_counter() - start) * 1000
    if audit: audit.record(task=task, model="demo-fallback", mode="demo", prompt=prompt, latency_ms=latency)
    return result, "demo", "demo-fallback"

def process_document(text: str, client: LemonadeClient | None = None,
                     audit: AuditLog | None = None) -> dict:
    if not text or not text.strip():
        raise ValueError("document text is empty")
    live = client if (client is not None and client.health()) else None
    mode = "real" if live else "demo"
    src = demo.detect_language(text)
    target = "en" if src == "ko" else "ko"
    target_name = "English" if target == "en" else "Korean"

    summary, _, model = _run_task("summarize", PROMPTS["summarize"].format(document=text),
                                  live, audit, lambda: demo.demo_summarize(text))
    translation, _, _ = _run_task("translate", PROMPTS["translate"].format(target_name=target_name, document=text),
                                  live, audit, lambda: demo.demo_translate(text, target))
    actions_raw, _, _ = _run_task("actions", PROMPTS["actions"].format(document=text),
                                  live, audit, lambda: "\n".join(demo.demo_action_items(text)))
    lines = [l.strip(" -\t") for l in actions_raw.splitlines() if l.strip()]
    if mode == "demo":
        lines = [l.replace("[DEMO] ", "") for l in lines]
    items = [{"id": f"A{i+1}", "text": t} for i, t in enumerate(lines)]
    return {
        "mode": mode, "model": model if mode == "real" else "demo-fallback",
        "demo_notice": None if mode == "real" else
            "DEMO/OFFLINE MODE: no Lemonade server was detected. Output below is a deterministic local fallback, NOT real Lemonade/model output.",
        "source_language": src, "target_language": target,
        "summary": summary, "translation": translation,
        "action_items": items,
    }
