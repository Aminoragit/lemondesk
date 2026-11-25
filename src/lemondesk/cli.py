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
    if a.file:
        try:
            text = open(a.file, encoding="utf-8").read()
        except OSError as e:
            print(f"Error: cannot read file '{a.file}': {e}", file=sys.stderr)
            return 2
    else:
        text = a.text or ""
    if a.file is None and a.text is None:
        p.error("provide --file or --text (or --check)")
    # An empty/whitespace document (from --file or --text) falls through to
    # process_document below, whose ValueError is reported gracefully as
    # "document text is empty" — not as a misleading argparse usage error.
    # Graceful errors, no tracebacks (BUG-3 fix): bad input is a user error,
    # reported as a clear message with a non-zero exit code.
    try:
        result = process_document(text, client=client, audit=AuditLog(a.audit))
    except ValueError as e:
        print(f"Error: {e}. Provide a non-empty document.", file=sys.stderr)
        return 2
    if result["demo_notice"]: print("⚠ " + result["demo_notice"])
    print(f"Mode: {result['mode']} | Model: {result['model']} | {result['source_language']} -> {result['target_language']}")
    print("\n== Summary ==\n" + result["summary"])
    print("\n== Translation ==\n" + result["translation"])
    print("\n== Action items (NOT exported until a human approves them) ==")
    for i in result["action_items"]: print(f"  {i['id']}: {i['text']}")
    gate = ApprovalGate(result["action_items"])
    for item_id in [x.strip() for x in a.approve.split(",") if x.strip()]:
        try:
            gate.approve(item_id)
        except KeyError:
            valid = ", ".join(i["id"] for i in result["action_items"]) or "(none)"
            print(f"Error: unknown action item ID '{item_id}'. Valid IDs: {valid}. Nothing was exported.", file=sys.stderr)
            return 2
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
