# AMD Lemonade Developer Challenge — Submission Pack (NOT submitted)

Status: local build only. No GitHub repo created, no form submitted. One pre-submit action remains: create the public GitHub repo, then replace the placeholder URL below.

## Exact text for the AMD form — "project details" field (paste as-is)

---

Project: LemonDesk — Local-first Korean-English AI work assistant powered by AMD Lemonade

Problem: Korean knowledge workers constantly need AI help with internal documents — summarize this report, translate it for a global teammate, pull out the action items. The documents that need this most are exactly the ones that must not be pasted into a cloud AI.

What I built: LemonDesk is an open-source (MIT) Python app (CLI + small web UI, zero third-party dependencies) that runs the whole workflow locally through AMD Lemonade's OpenAI-compatible API. It detects a running Lemonade server (health check + GET /api/v1/models), then routes each reasoning step through Lemonade chat completions as a separate, task-specific call: (1) summarize, (2) translate KO->EN or EN->KO (direction auto-detected), (3) extract action items. Lemonade is the inference engine inside the loop for all three steps — not a logo on the page.

Two structural safeguards: (1) a human approval gate — extracted action items are never exported until a human approves specific item IDs; export is deterministic code, and the model never decides what gets exported (test-proven: 0 approvals = 0 exported items). (2) an audit log — every model call is appended to a JSONL log with timestamp, model, mode, SHA-256 prompt hash, and latency.

If no Lemonade server is present, LemonDesk runs in a clearly labelled DEMO/OFFLINE mode using a deterministic local fallback; demo output is always marked [DEMO] and is never presented as real model output. This lets any reviewer reproduce the full workflow, approval gate included, on any machine.

Verification: 13 automated tests, all passing (measured 2026-11-25, Python 3.12.3), including an end-to-end run of the workflow against a separate fake Lemonade server implementing the same OpenAI-compatible endpoints. Honest limitation: this build was developed on a machine without a Lemonade server, so real-mode behaviour is proven against that faithful test double, not yet benchmarked on physical Ryzen AI hardware — that benchmark is the stated next step.

Links: GitHub repository (open source, MIT): <PASTE GITHUB REPO URL HERE>
Demo: run `python3 -m lemondesk.cli --file examples/sample-ko.txt` (demo mode, no server needed) or `python3 -m lemondesk.server` for the web UI — see README.md for full instructions, architecture, test results, and disclosed limitations.

---

## Form fields (from the information the entrant provided)

- First name: Seokwon / Last name: Choi
- Email: wjsxkxk1@gmail.com
- Company: Independent developer
- Country: Republic of Korea / City: Seoul
- GitHub ID: <TO FILL at submit time> / Discord ID: <TO FILL at submit time>

## Quality gate self-score (~/workspace/quality-gate/SUBMISSION-QUALITY-CHECKLIST.md)

Adversarial self-scoring, evidence in this package. The AMD challenge has no downloadable form template — the form is a web form with a free-text project-details field — so Category A is scored on exact use of that field and completeness of required information, not on a recreated template (no template was recreated).

| Category | Score | Evidence / deductions |
|---|---|---|
| A. Form compliance | 20/20 | Exact paste-ready text for the official project-details field above; all other form fields listed; nothing reformatted or invented |
| B. Idea / problem definition | 14/15 | Concrete opening scene, named audience, one-sentence difference vs cloud AI, hypothesis reversal (translator → local+accountable loop). −1: no field-interview quotes or market statistics yet |
| C. Logic / architecture | 20/20 | Step-by-step pipeline diagram; per-task model roles; boundary declaration ("model never decides what gets exported"); structural (not prompt) approval gate; independent fake-server verifier; per-call audit log; Lemonade inside the reasoning loop; full Built With |
| D. Execution / proof | 18/20 | Working code; 13/13 tests actually run and counted; reproducible deterministic demo; CLI + web UI smoke-tested live. −2: no run on physical Lemonade/Ryzen AI hardware yet, no external users — both disclosed, none fabricated |
| E. Narrative / completeness | 15/15 | All sections filled; tagline; honest Challenges; project-specific lessons; "what we chose not to build" stated; What's Next expands to a broader pattern, not a feature list |
| F. Pre-submit verification | 10/10 | Tests re-run at packaging; files inventoried; eligibility re-confirmed by the entrant (Korea eligible per entrant's direct confirmation, correcting the US/Canada-only footnote reading); single remaining action (GitHub URL) explicitly flagged rather than hidden |
| **Total** | **97/100 — PASS (≥96)** | |

Iteration log: v1 draft scored 94 (D penalised for unproven export gate and missing verifier) → added fake-server end-to-end test, structural-gate tests, and live CLI/UI smoke runs → re-scored 97.
