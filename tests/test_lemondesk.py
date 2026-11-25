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

if __name__ == "__main__":
    unittest.main(verbosity=2)
