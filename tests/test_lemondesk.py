import json, os, sys, tempfile, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from lemondesk.audit import AuditLog, prompt_hash
from lemondesk.client import LemonadeClient
from lemondesk import demo
from lemondesk.workflow import ApprovalGate, process_document

KO_DOC = "회의 보고서를 준비해야 합니다. 금요일까지 검토 보고서를 보내주세요. 프로젝트 일정은 다음 주에 공유됩니다."
EN_DOC = "Please review the report by Friday. The deadline is Monday. We will discuss the schedule in the meeting."

class FakeLemonade(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _json(self, obj):
        b = json.dumps(obj).encode(); self.send_response(200)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path.endswith("/health"): self._json({"status": "ok"})
        elif self.path.endswith("/models"): self._json({"data": [{"id": "fake-model-1"}]})
        else: self.send_response(404); self.end_headers()
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); body = json.loads(self.rfile.read(n) or b"{}")
        prompt = body["messages"][0]["content"]
        if prompt.startswith("Summarize"): content = "FAKE SUMMARY"
        elif prompt.startswith("Translate"): content = "FAKE TRANSLATION"
        elif prompt.startswith("Extract"): content = "Do the first thing\nDo the second thing"
        else: content = "?"
        self._json({"choices": [{"message": {"content": content}}]})

def start_fake():
    srv = HTTPServer(("127.0.0.1", 0), FakeLemonade)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/api/v1"

class TestDemo(unittest.TestCase):
    def test_demo_is_deterministic(self):
        self.assertEqual(demo.demo_summarize(KO_DOC), demo.demo_summarize(KO_DOC))
        self.assertEqual(demo.demo_translate(EN_DOC, "ko"), demo.demo_translate(EN_DOC, "ko"))
    def test_demo_output_is_labelled(self):
        self.assertTrue(demo.demo_summarize(EN_DOC).startswith("[DEMO]"))
        self.assertTrue(demo.demo_translate(EN_DOC, "ko").startswith("[DEMO]"))
    def test_detect_language(self):
        self.assertEqual(demo.detect_language(KO_DOC), "ko")
        self.assertEqual(demo.detect_language(EN_DOC), "en")
    def test_demo_action_extraction_ko_and_en(self):
        self.assertTrue(len(demo.demo_action_items(KO_DOC)) >= 1)
        self.assertTrue(len(demo.demo_action_items(EN_DOC)) >= 1)

class TestApprovalGate(unittest.TestCase):
    ITEMS = [{"id": "A1", "text": "x"}, {"id": "A2", "text": "y"}, {"id": "A3", "text": "z"}]
    def test_zero_approvals_zero_exported(self):
        self.assertEqual(ApprovalGate(list(self.ITEMS)).export(), [])
    def test_only_approved_are_exported(self):
        g = ApprovalGate(list(self.ITEMS)); g.approve("A2")
        self.assertEqual([i["id"] for i in g.export()], ["A2"])
    def test_unknown_id_rejected(self):
        with self.assertRaises(KeyError): ApprovalGate(list(self.ITEMS)).approve("A99")

class TestAudit(unittest.TestCase):
    def test_audit_written_with_hash_and_mode(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "a.jsonl"); log = AuditLog(path)
            e = log.record(task="summarize", model="m", mode="demo", prompt="hello", latency_ms=1.5)
            rows = log.read_all(); self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["prompt_hash"], prompt_hash("hello"))
            self.assertEqual(rows[0]["mode"], "demo"); self.assertIn("timestamp", e)
    def test_audit_rejects_bad_mode(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                AuditLog(os.path.join(d, "a.jsonl")).record(task="t", model="m", mode="fake", prompt="p", latency_ms=0)

class TestRealModeWithFakeServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.srv, cls.base = start_fake()
    @classmethod
    def tearDownClass(cls): cls.srv.shutdown()
    def test_health_and_models(self):
        c = LemonadeClient(self.base, timeout=2)
        self.assertTrue(c.health()); self.assertEqual(c.list_models(), ["fake-model-1"])
    def test_workflow_uses_lemonade_inside_loop(self):
        with tempfile.TemporaryDirectory() as d:
            audit = AuditLog(os.path.join(d, "a.jsonl"))
            r = process_document(EN_DOC, client=LemonadeClient(self.base, timeout=2), audit=audit)
            self.assertEqual(r["mode"], "real"); self.assertEqual(r["model"], "fake-model-1")
            self.assertEqual(r["summary"], "FAKE SUMMARY"); self.assertEqual(r["translation"], "FAKE TRANSLATION")
            self.assertEqual([i["id"] for i in r["action_items"]], ["A1", "A2"])
            rows = audit.read_all(); self.assertEqual(len(rows), 3)
            self.assertTrue(all(x["mode"] == "real" for x in rows))

class TestOfflineMode(unittest.TestCase):
    def test_no_server_means_clearly_labelled_demo(self):
        c = LemonadeClient("http://127.0.0.1:9/api/v1", timeout=0.5)
        self.assertFalse(c.health())
        with tempfile.TemporaryDirectory() as d:
            audit = AuditLog(os.path.join(d, "a.jsonl"))
            r = process_document(KO_DOC, client=c, audit=audit)
            self.assertEqual(r["mode"], "demo"); self.assertIsNotNone(r["demo_notice"])
            self.assertIn("NOT real Lemonade", r["demo_notice"])
            self.assertTrue(all(x["mode"] == "demo" for x in audit.read_all()))
    def test_empty_document_rejected(self):
        with self.assertRaises(ValueError): process_document("  ")

# ---------------------------------------------------------------------------
# Regression tests added after the independent evaluation (../EVALUATION.md).
# Each class maps to a numbered bug in that report.
# ---------------------------------------------------------------------------
import contextlib, io, urllib.request, urllib.error
from urllib.parse import urlencode
from lemondesk.cli import main as cli_main
from lemondesk.server import make_handler

class FlakyLemonade(BaseHTTPRequestHandler):
    """Answers everything except Translate, which returns HTTP 500 (BUG-1)."""
    def log_message(self, *a): pass
    def _json(self, obj):
        b = json.dumps(obj).encode(); self.send_response(200)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path.endswith("/health"): self._json({"status": "ok"})
        elif self.path.endswith("/models"): self._json({"data": [{"id": "fake-model-1"}]})
        else: self.send_response(404); self.end_headers()
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); body = json.loads(self.rfile.read(n) or b"{}")
        prompt = body["messages"][0]["content"]
        if prompt.startswith("Translate"):
            b = b"flaky translate failure"; self.send_response(500)
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
        if prompt.startswith("Summarize"): content = "FAKE SUMMARY"
        elif prompt.startswith("Extract"): content = "Do the first thing\nDo the second thing"
        else: content = "?"
        self._json({"choices": [{"message": {"content": content}}]})

def start_flaky():
    srv = HTTPServer(("127.0.0.1", 0), FlakyLemonade)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/api/v1"

class TestMixedModeLabelling(unittest.TestCase):
    """BUG-1: a partial fallback must be reported as mixed, never pure real."""
    @classmethod
    def setUpClass(cls): cls.srv, cls.base = start_flaky()
    @classmethod
    def tearDownClass(cls): cls.srv.shutdown()
    def test_partial_fallback_is_mixed_and_audited_consistently(self):
        with tempfile.TemporaryDirectory() as d:
            audit = AuditLog(os.path.join(d, "a.jsonl"))
            r = process_document(EN_DOC, client=LemonadeClient(self.base, timeout=2), audit=audit)
            self.assertEqual(r["mode"], "mixed")
            self.assertEqual(r["task_modes"], {"summarize": "real", "translate": "demo", "actions": "real"})
            self.assertIsNotNone(r["demo_notice"]); self.assertIn("MIXED MODE", r["demo_notice"])
            self.assertIn("translate", r["demo_notice"])
            self.assertTrue(r["translation"].startswith("[DEMO]"))
            self.assertEqual(r["summary"], "FAKE SUMMARY")
            rows = {x["task"]: x["mode"] for x in audit.read_all()}
            self.assertEqual(rows, r["task_modes"])  # audit and result cannot disagree

class CountingLemonade(FakeLemonade):
    models_hits = 0
    def do_GET(self):
        if self.path.endswith("/models"): type(self).models_hits += 1
        super().do_GET()

class TestClientModelCache(unittest.TestCase):
    """BUG-7: chat() must not re-list models on every call."""
    @classmethod
    def setUpClass(cls):
        CountingLemonade.models_hits = 0
        cls.srv = HTTPServer(("127.0.0.1", 0), CountingLemonade)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}/api/v1"
    @classmethod
    def tearDownClass(cls): cls.srv.shutdown()
    def test_models_listed_once_for_repeated_chats(self):
        c = LemonadeClient(self.base, timeout=2)
        c.chat([{"role": "user", "content": "Summarize x"}])
        c.chat([{"role": "user", "content": "Summarize y"}])
        self.assertEqual(CountingLemonade.models_hits, 1)

class TestDemoExtractorBareJuseyo(unittest.TestCase):
    """BUG-4: bare 주세요/보내주세요 requests must be extracted."""
    def test_bare_juseyo_sentence_extracted(self):
        self.assertTrue(demo.demo_action_items("자료를 메일로 보내주세요."))
        self.assertTrue(demo.demo_action_items("일정을 확인해 주세요."))
    def test_project_sample_extracts_send_request(self):
        path = os.path.join(os.path.dirname(__file__), "..", "examples", "sample-ko.txt")
        with open(path, encoding="utf-8") as f: sample = f.read()
        items = demo.demo_action_items(sample)
        self.assertTrue(any("보내주세요" in i for i in items), items)

class TestCliGracefulErrors(unittest.TestCase):
    """BUG-3 (CLI): bad input -> clear error + non-zero exit, no traceback."""
    def test_empty_document_is_graceful(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = cli_main(["--text", "   "])
        self.assertEqual(rc, 2); self.assertIn("Error", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())
    def test_unknown_approve_id_is_graceful(self):
        with tempfile.TemporaryDirectory() as d:
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                rc = cli_main(["--text", KO_DOC, "--approve", "A99",
                               "--audit", os.path.join(d, "a.jsonl")])
        self.assertEqual(rc, 2); self.assertIn("unknown action item ID 'A99'", err.getvalue())

def start_ui(audit_path):
    srv = HTTPServer(("127.0.0.1", 0), make_handler(audit_path))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"

def post_form(url, data):
    req = urllib.request.Request(url, data=urlencode(data, doseq=True).encode())
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")

class TestServerExportTrust(unittest.TestCase):
    """BUG-2 + BUG-3 (server): export only ever releases server-extracted items."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.srv, self.base = start_ui(os.path.join(self.tmp.name, "a.jsonl"))
    def tearDown(self):
        self.srv.shutdown(); self.srv.server_close(); self.tmp.cleanup()
    def test_export_without_any_process_is_rejected(self):
        status, body = post_form(self.base + "/export",
                                 {"items": '[{"id":"X1","text":"FORGED never extracted"}]', "approve": "X1"})
        self.assertEqual(status, 400); self.assertNotIn("Exported", body)
    def test_forged_id_rejected_and_posted_items_ignored(self):
        status, _ = post_form(self.base + "/process", {"text": KO_DOC})
        self.assertEqual(status, 200)
        status, body = post_form(self.base + "/export",
                                 {"items": '[{"id":"X1","text":"FORGED never extracted"}]', "approve": "X1"})
        self.assertEqual(status, 400); self.assertIn("unknown action item", body)
        self.assertNotIn("FORGED", body)
        # Even with a forged items field present, approving a real ID exports
        # the SERVER-side item text, never client-supplied text.
        status, body = post_form(self.base + "/export",
                                 {"items": '[{"id":"A1","text":"FORGED replacement"}]', "approve": "A1"})
        self.assertEqual(status, 200); self.assertIn("Exported 1 approved item(s)", body)
        self.assertIn("준비해야 합니다", body); self.assertNotIn("FORGED replacement", body)
    def test_empty_process_returns_http_400_page(self):
        status, body = post_form(self.base + "/process", {"text": ""})
        self.assertEqual(status, 400); self.assertIn("Error", body)

if __name__ == "__main__":
    unittest.main(verbosity=2)
