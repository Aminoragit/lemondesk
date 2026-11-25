"""Tiny stdlib web UI: python -m lemondesk.server [--port 8765]
Paste a document -> summary/translation/action items -> tick approvals -> export.
Export re-checks approvals server-side through the same ApprovalGate."""
from __future__ import annotations
import argparse, html, json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from .audit import AuditLog
from .client import LemonadeClient
from .workflow import ApprovalGate, process_document

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>LemonDesk — powered by AMD Lemonade</title></head><body>
<h1>LemonDesk</h1><p>Local-first Korean–English AI work assistant powered by <b>AMD Lemonade</b>. Documents never leave this machine when Lemonade is local.</p>
<form method="post" action="/process"><textarea name="text" rows="12" cols="90" placeholder="Paste a Korean or English document...">{text}</textarea><br>
<button type="submit">Summarize + Translate + Extract action items</button></form>
{result}</body></html>"""

def render_result(r: dict) -> str:
    notice = f"<p><b>⚠ {html.escape(r['demo_notice'])}</b></p>" if r["demo_notice"] else ""
    items = "".join(
        f'<label><input type="checkbox" name="approve" value="{i["id"]}"> {i["id"]}: {html.escape(i["text"])}</label><br>'
        for i in r["action_items"])
    return (f"{notice}<p>Mode: <b>{r['mode']}</b> | Model: {html.escape(str(r['model']))}</p>"
            f"<h2>Summary</h2><p>{html.escape(r['summary'])}</p>"
            f"<h2>Translation ({r['source_language']} → {r['target_language']})</h2><p>{html.escape(r['translation'])}</p>"
            f"<h2>Action items — human approval required before export</h2>"
            f'<form method="post" action="/export">{items}'
            f'<input type="hidden" name="items" value="{html.escape(json.dumps(r["action_items"]), quote=True)}">'
            f'<button type="submit">Export approved only</button></form>')

def make_handler(audit_path="audit.jsonl"):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def _send(self, body: str):
            b = body.encode("utf-8"); self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        def do_GET(self):
            self._send(PAGE.format(text="", result=""))
        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            form = parse_qs(self.rfile.read(n).decode("utf-8"))
            if self.path == "/process":
                text = form.get("text", [""])[0]
                r = process_document(text, client=LemonadeClient(), audit=AuditLog(audit_path))
                self._send(PAGE.format(text=html.escape(text), result=render_result(r)))
            elif self.path == "/export":
                items = json.loads(form.get("items", ["[]"])[0])
                gate = ApprovalGate(items)
                for item_id in form.get("approve", []): gate.approve(item_id)
                self._send(f"<h1>Exported {len(gate.export())} approved item(s)</h1><pre>{html.escape(gate.export_json())}</pre><p><a href='/'>Back</a></p>")
            else:
                self.send_response(404); self.end_headers()
    return H

def main(argv=None):
    p = argparse.ArgumentParser(prog="lemondesk-server"); p.add_argument("--port", type=int, default=8765); p.add_argument("--audit", default="audit.jsonl")
    a = p.parse_args(argv)
    print(f"LemonDesk web UI at http://127.0.0.1:{a.port}")
    HTTPServer(("127.0.0.1", a.port), make_handler(a.audit)).serve_forever()

if __name__ == "__main__":
    main()
