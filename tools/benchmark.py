"""LemonDesk real-hardware benchmark — stdlib only, no pip installs.

Run this on a machine with a REAL Lemonade server running. It calls
LemonDesk's own workflow (process_document) on two Korean documents:

  1. the project's bundled sample   (project/examples/sample-ko.txt)
  2. a longer meeting-notes document (tools/sample-long-ko.txt, bundled
     next to this script)

For each document it records, from LemonDesk's own audit log (the same
JSONL rows the app always writes): per-task latency, per-task mode,
model name, plus wall-clock total time. It then writes BENCHMARK-RESULT.md
with a fill-in machine-spec table and the measured numbers.

Honesty rules built in:
- Latencies are the audit log's own per-call measurements; nothing is
  estimated, and no token counts are invented (LemonDesk's client does
  not receive token usage, so this script reports characters, not tokens).
- If the run's mode is not "real" (demo or mixed), the result file says
  so in a prominent warning — demo numbers must never be presented as
  real-hardware results.

Usage (from this tools/ folder, Lemonade server running):
    python benchmark.py
    python benchmark.py --base-url http://localhost:13305/api/v1
    python benchmark.py --output BENCHMARK-RESULT.md

Exit code 0 = result file written (check its mode warning).
Exit code 2 = LemonDesk project not found / input file missing.
"""
from __future__ import annotations

import argparse
import os
import platform
import sys
import tempfile
import time
from datetime import datetime, timezone

KIT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROJECT = os.path.normpath(os.path.join(KIT_DIR, "..", "project"))
# When this script lives in the repo at project/tools/, the project root is
# KIT_DIR's parent itself; find_project() tries that candidate first.
IN_REPO_PROJECT = os.path.normpath(os.path.join(KIT_DIR, ".."))


def find_project(cli_value: str | None) -> str | None:
    """Locate the LemonDesk project dir (the one containing src/lemondesk)."""
    candidates = []
    if cli_value:
        candidates.append(cli_value)
    env = os.environ.get("LEMONDESK_PROJECT")
    if env:
        candidates.append(env)
    candidates += [IN_REPO_PROJECT, DEFAULT_PROJECT, os.path.join(os.getcwd(), "project"), os.getcwd()]
    for c in candidates:
        if os.path.isdir(os.path.join(c, "src", "lemondesk")):
            return os.path.abspath(c)
    return None


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="benchmark",
        description="Benchmark LemonDesk against a live Lemonade server.")
    p.add_argument("--base-url", default=None,
                   help="Lemonade base URL (default: $LEMONADE_BASE_URL or "
                        "http://localhost:13305/api/v1)")
    p.add_argument("--project-dir", default=None,
                   help="path to the lemondesk project (default: ../project "
                        "relative to this kit, or $LEMONDESK_PROJECT)")
    p.add_argument("--output", default=os.path.join(KIT_DIR, "BENCHMARK-RESULT.md"),
                   help="where to write the result markdown")
    p.add_argument("--runs", type=int, default=1,
                   help="repeat each document this many times and report "
                        "every run (default 1; use 2-3 on real hardware and "
                        "ignore the first, cold-start run)")
    a = p.parse_args(argv)
    if a.runs < 1:
        p.error("--runs must be >= 1")

    project = find_project(a.project_dir)
    if project is None:
        print("Error: LemonDesk project not found (looked for src/lemondesk). "
              "Clone https://github.com/Aminoragit/lemondesk or pass "
              "--project-dir / set LEMONDESK_PROJECT.", file=sys.stderr)
        return 2
    sys.path.insert(0, os.path.join(project, "src"))

    from lemondesk.audit import AuditLog
    from lemondesk.client import LemonadeClient
    from lemondesk.workflow import process_document

    docs = [
        ("Bundled sample (project/examples/sample-ko.txt)",
         os.path.join(project, "examples", "sample-ko.txt")),
        ("Long meeting notes (tools/sample-long-ko.txt)",
         os.path.join(KIT_DIR, "sample-long-ko.txt")),
    ]
    for _, path in docs:
        if not os.path.exists(path):
            print(f"Error: input document missing: {path}", file=sys.stderr)
            return 2

    client = LemonadeClient(a.base_url) if a.base_url else LemonadeClient()
    reachable = client.health()
    models = []
    if reachable:
        try:
            models = client.list_models()
        except Exception:
            models = []

    results = []  # one dict per (document, run)
    with tempfile.TemporaryDirectory() as td:
        audit_path = os.path.join(td, "benchmark-audit.jsonl")
        for label, path in docs:
            text = open(path, encoding="utf-8").read()
            for run_no in range(1, a.runs + 1):
                audit = AuditLog(audit_path)
                before = len(audit.read_all())
                start = time.perf_counter()
                result = process_document(text, client=client, audit=audit)
                wall_s = time.perf_counter() - start
                rows = audit.read_all()[before:]
                per_task = {}
                for r in rows:
                    per_task[r["task"]] = {
                        "latency_ms": r["latency_ms"], "mode": r["mode"],
                        "model": r["model"],
                    }
                results.append({
                    "label": label, "run": run_no, "chars": len(text),
                    "wall_s": wall_s, "mode": result["mode"],
                    "task_modes": result["task_modes"],
                    "model": result["model"],
                    "summary_chars": len(result["summary"]),
                    "translation_chars": len(result["translation"]),
                    "action_items": len(result["action_items"]),
                    "per_task": per_task, "audit_rows": len(rows),
                })
                print(f"[{label} / run {run_no}] mode={result['mode']} "
                      f"model={result['model']} wall={wall_s:.2f}s "
                      f"audit_rows={len(rows)}")

    overall_mode = ("real" if all(r["mode"] == "real" for r in results)
                    else "demo" if all(r["mode"] == "demo" for r in results)
                    else "mixed")
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    lines = []
    lines.append("# LemonDesk — Benchmark Result")
    lines.append("")
    lines.append(f"- **Measured at:** {now}")
    lines.append(f"- **Lemonade base URL:** {client.base_url}")
    lines.append(f"- **Server reachable (health check):** {'yes' if reachable else 'NO'}")
    lines.append(f"- **Models reported by server:** {', '.join(models) if models else '(none / unreachable)'}")
    lines.append(f"- **Overall mode:** **{overall_mode}**")
    lines.append("")
    if overall_mode != "real":
        lines.append("> ⚠️ **WARNING — NOT REAL-HARDWARE RESULTS.** This run's mode is "
                     f"`{overall_mode}`, meaning some or all tasks were served by "
                     "LemonDesk's deterministic DEMO fallback, not by a Lemonade model. "
                     "These numbers measure the fallback code path only. Re-run with a "
                     "real Lemonade server (see RUN-GUIDE.ko.md) before quoting any number.")
        lines.append("")
    lines.append("## Machine specs (fill in by hand before sharing)")
    lines.append("")
    lines.append("| Item | Value |")
    lines.append("|---|---|")
    lines.append("| CPU / APU | _(fill in — e.g. AMD Ryzen AI Max+ 395 / Ryzen AI 9 HX 370 / …)_ |")
    lines.append("| GPU / NPU actually used | _(fill in — check Lemonade's monitor/status)_ |")
    lines.append("| RAM | _(fill in — e.g. 32 GB)_ |")
    lines.append("| OS | _(fill in — e.g. Windows 11 Pro 24H2)_ |")
    lines.append(f"| Python | {platform.python_version()} (auto-filled) |")
    lines.append("| Lemonade version | _(fill in — `lemonade status` or the app's About)_ |")
    lines.append("| Backend / recipe | _(fill in — e.g. llamacpp / vulkan or rocm)_ |")
    lines.append("| Power mode | _(fill in — plugged in? performance mode?)_ |")
    lines.append("")
    lines.append("## Measured results")
    lines.append("")
    lines.append("Per-task latency is LemonDesk's own audit-log measurement for each "
                 "Lemonade chat completion (summarize / translate / actions). "
                 "Output size is in characters — LemonDesk's client does not receive "
                 "token usage, so no token figures are reported or estimated.")
    lines.append("")
    for r in results:
        lines.append(f"### {r['label']} — run {r['run']}")
        lines.append("")
        lines.append(f"- Document: {r['chars']} chars | Wall-clock total: **{r['wall_s']:.2f} s** "
                     f"| Mode: **{r['mode']}** | Model: `{r['model']}` | Audit rows: {r['audit_rows']}")
        lines.append(f"- Output: summary {r['summary_chars']} chars, "
                     f"translation {r['translation_chars']} chars, "
                     f"action items {r['action_items']}")
        lines.append("")
        lines.append("| Task | Mode | Latency (audit log) |")
        lines.append("|---|---|---|")
        for task in ("summarize", "translate", "actions"):
            t = r["per_task"].get(task)
            if t:
                lines.append(f"| {task} | {t['mode']} | {t['latency_ms']:.1f} ms |")
            else:
                lines.append(f"| {task} | — | (no audit row) |")
        lines.append("")
    lines.append("## How to share this result")
    lines.append("")
    lines.append("1. Fill in the machine-spec table above — a benchmark without the "
                 "machine is not reproducible.")
    lines.append("2. If mode is `real`, copy this file into the repo (e.g. "
                 "`docs/BENCHMARK-RESULT.md`) or attach it to the README update, "
                 "exactly as measured — do not round away the slow cold-start run; "
                 "label it instead.")
    lines.append("3. Keep the audit JSONL from the same session if you can — it is "
                 "the raw evidence behind every number above.")
    lines.append("")

    with open(a.output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nWrote {a.output} (overall mode: {overall_mode})")
    if overall_mode != "real":
        print("NOTE: mode is not 'real' — the result file carries a DEMO warning "
              "and must not be quoted as real-hardware performance.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
