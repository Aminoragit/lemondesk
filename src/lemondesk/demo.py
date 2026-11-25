"""Deterministic OFFLINE/DEMO fallback. NOT a model. Output is always labelled DEMO.

Strategies (deterministic, no randomness, no network):
- summarize: extractive — the first 3 sentences of the document, joined in order
  (see demo_summarize; it does not look at paragraphs at all).
- translate: sentence-level glossary substitution for a small fixed KO<->EN glossary,
  otherwise the source sentence is returned prefixed with [DEMO-untranslated].
- action items: lines/sentences matching explicit request/task markers (TODO, 해야,
  해주세요, bare 주세요/보내주세요-style requests, please, deadline, 마감, etc.).
"""
from __future__ import annotations
import re

GLOSSARY_EN_KO = {
    "meeting": "회의", "report": "보고서", "deadline": "마감", "review": "검토",
    "send": "보내기", "prepare": "준비", "document": "문서", "schedule": "일정",
    "team": "팀", "project": "프로젝트",
}
GLOSSARY_KO_EN = {v: k for k, v in GLOSSARY_EN_KO.items()}
ACTION_PATTERNS = [
    r"TODO[:\s].+", r".*해야 합니다.*", r".*해주세요.*", r".*해 주세요.*",
    # Bare polite requests (BUG-4 fix): "보내주세요", "확인해 주세요" without the
    # "해" — e.g. the project's own sample "검토 보고서를 팀에 보내주세요" was missed.
    r".*주세요.*", r".*주십시오.*", r".*주시기 바랍니다.*",
    r"(?i).*please .+", r"(?i).*deadline.*", r".*마감.*", r"(?i).*action item.*",
]

def split_sentences(text: str) -> list:
    parts = re.split(r"(?<=[.!?。])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]

def detect_language(text: str) -> str:
    return "ko" if re.search(r"[가-힣]", text) else "en"

def demo_summarize(text: str) -> str:
    sents = split_sentences(text)
    return "[DEMO] " + " ".join(sents[:3])

def demo_translate(text: str, target: str) -> str:
    glossary = GLOSSARY_KO_EN if target == "en" else GLOSSARY_EN_KO
    out = []
    for sent in split_sentences(text):
        translated = sent
        hit = False
        for src, dst in glossary.items():
            if src in translated:
                translated = translated.replace(src, dst); hit = True
        out.append(translated if hit else f"[DEMO-untranslated] {sent}")
    return "[DEMO] " + " ".join(out)

def demo_action_items(text: str) -> list:
    items = []
    for sent in split_sentences(text):
        if any(re.match(p, sent) or re.search(p, sent) for p in ACTION_PATTERNS):
            items.append(sent)
    return items
