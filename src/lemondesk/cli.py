"""CLI: python -m lemondesk.cli --check | --file doc.txt [--approve A1,A2] [--audit audit.jsonl]"""
from __future__ import annotations
import argparse, json, sys
from .audit import AuditLog
from .client import LemonadeClient, LemonadeUnavailable
from .workflow import ApprovalGate, process_document

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="lemondesk", description="LemonDesk — local-first KO/EN AI work assistant powered by AMD Lemonade")
    p.add_argument("--base-url", default=None, help="Lemonade base URL (default http://localhost:13305/api/v1)")
    p.add_argument("--check", action="store_true", help="detect Lemonade and list models, then exit")
    p.add_argument("--file", help="UTF-8 text file to process")
    p.add_argument("--text", help="inline document text to process")
    p.add_argument("--approve", default="", help="comma-separated action item IDs a HUMAN approves for export, e.g. A1,A3")
    p.add_argument("--audit", default="audit.jsonl", help="audit log path (JSONL)")
    p.add_argument("--export", default=None, help="write approved action items JSON to this path (only approved items)")
    a = p.parse_args(argv)
    client = LemonadeClient(a.base_url) if a.base_url else LemonadeClient()
    if a.check:
        alive = client.health()
        print(f"Lemonade at {client.base_url}: {'REACHABLE' if alive else 'NOT REACHABLE (demo mode will be used)'}")
        if alive:
            try: print("Models:", ", ".join(client.list_models()) or "(none reported)")
            except LemonadeUnavailable as e: print("Models: unavailable -", e)
        return 0
    text = open(a.file, encoding="utf-8").read() if a.file else (a.text or "")
    if not text:
        p.error("provide --file or --text (or --check)")
    result = process_document(text, client=client, audit=AuditLog(a.audit))
    if result["demo_notice"]: print("⚠ " + result["demo_notice"])
    print(f"Mode: {result['mode']} | Model: {result['model']} | {result['source_language']} -> {result['target_language']}")
    print("\n== Summary ==\n" + result["summary"])
    print("\n== Translation ==\n" + result["translation"])
    print("\n== Action items (NOT exported until a human approves them) ==")
    for i in result["action_items"]: print(f"  {i['id']}: {i['text']}")
    gate = ApprovalGate(result["action_items"])
    for item_id in [x.strip() for x in a.approve.split(",") if x.strip()]:
        gate.approve(item_id)
    exported = gate.export()
    print(f"\nApproved: {len(gate.approved)} | Exported: {len(exported)}")
    if a.export:
        with open(a.export, "w", encoding="utf-8") as f: f.write(gate.export_json())
        print(f"Exported approved items -> {a.export}")
    elif exported:
        print(gate.export_json())
    return 0

if __name__ == "__main__":
    sys.exit(main())
