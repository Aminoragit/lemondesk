# AMD Lemonade Developer Challenge — Submission Record

**Status: SUBMITTED on 2026-11-25.** AMD's confirmation page responded with
**"Your Submission has Been Received."** The GitHub repository is public at
https://github.com/Aminoragit/lemondesk — remediation of the issues found by
independent post-submission evaluation is in progress in that repository (see
"Post-submission evaluation and remediation" below).

## Form fields (as submitted)

- First name: Seokwon / Last name: Choi
- Email: wjsxkxk1@gmail.com
- Company: Independent developer
- Country: Republic of Korea / City: Seoul
- GitHub ID: **Aminoragit**
- Discord ID: **aminora.**

## Exact text submitted in the AMD form's "project details" field

---

Project: LemonDesk — Local-first Korean-English AI work assistant powered by AMD Lemonade

Problem: Korean knowledge workers constantly need AI help with internal documents — summarize this report, translate it for a global teammate, pull out the action items. The documents that need this most are exactly the ones that must not be pasted into a cloud AI.

What I built: LemonDesk is an open-source (MIT) Python app (CLI + small web UI, zero third-party dependencies) that runs the whole workflow locally through AMD Lemonade's OpenAI-compatible API. It detects a running Lemonade server (health check + GET /api/v1/models), then routes each reasoning step through Lemonade chat completions as a separate, task-specific call: (1) summarize, (2) translate KO->EN or EN->KO (direction auto-detected), (3) extract action items. Lemonade is the inference engine inside the loop for all three steps — not a logo on the page.

Two structural safeguards: (1) a human approval gate — extracted action items are never exported until a human approves specific item IDs; export is deterministic code, and the model never decides what gets exported (test-proven: 0 approvals = 0 exported items). (2) an audit log — every model call is appended to a JSONL log with timestamp, model, mode, SHA-256 prompt hash, and latency.

If no Lemonade server is present, LemonDesk runs in a clearly labelled DEMO/OFFLINE mode using a deterministic local fallback; demo output is always marked [DEMO] and is never presented as real model output. This lets any reviewer reproduce the full workflow, approval gate included, on any machine.

Verification: 13 automated tests, all passing (measured 2026-11-25, Python 3.12.3), including an end-to-end run of the workflow against a separate fake Lemonade server implementing the same OpenAI-compatible endpoints. Honest limitation: this build was developed on a machine without a Lemonade server, so real-mode behaviour is proven against that faithful test double, not yet benchmarked on physical Ryzen AI hardware — that benchmark is the stated next step.

Links: GitHub repository (open source, MIT): https://github.com/Aminoragit/lemondesk
Demo: run `python3 -m lemondesk.cli --file examples/sample-ko.txt` (demo mode, no server needed) or `python3 -m lemondesk.server` for the web UI — see README.md for full instructions, architecture, test results, and disclosed limitations.

---

(The test count of 13 above was accurate at submission time; the suite has
since grown to 26 tests during remediation — see below. The form text itself
is a historical record and is not edited retroactively.)

## Post-submission evaluation and remediation

After submission, an **independent adversarial evaluation** scored this entry
against the project's own submission quality checklist
(`~/workspace/quality-gate/SUBMISSION-QUALITY-CHECKLIST.md`):

- **Independent evaluation result (round 1): 58/100 — FAIL** (full report:
  [`EVALUATION.md`](EVALUATION.md), in this repository).
  This supersedes the pre-submission self-score of 97/100, which the evaluator
  overturned as inflated — chiefly in Execution/proof (18 → 5) and Idea (14 → 5.5):
  no demo video or screenshots, no problem-size statistics, no external users,
  AMD's judging criteria never explicitly addressed, and four real bugs found
  by probing. No fabricated numbers were found; every quantitative claim that
  existed (13/13 tests, gate behaviour, audit fields, endpoints) re-verified as true.

- **Independent re-evaluation result (round 2): 71/100 — FAIL** (full report:
  [`EVALUATION-2.md`](EVALUATION-2.md), in this repository). The round-2
  evaluator independently re-probed every round-1 bug fix (all held, including
  a mixed-mode probe on a task the remediation's own test did not cover),
  verified all three cited statistics at their sources, and confirmed the
  live repository was byte-identical to the local project. Remaining
  deductions sit almost entirely in Execution/proof: no real-hardware run,
  no demo video, no real users. Its in-repo fix list has also been applied
  (see the round-2 items below); the rest cannot be closed from a repository.

- **Remediation in progress / applied locally (post-submission):**
  - BUG-1 (mixed-mode mislabelling): fixed — runs now report `real` / `demo` /
    `mixed` from per-task outcomes, with the fallen-back tasks named in the
    notice and audit modes consistent with the result. Regression-tested
    against a deliberately flaky fake server.
  - BUG-2 (forgeable web /export): fixed — exportable items live only in
    server-side state from the server's own `/process` run; forged IDs/items
    are rejected with HTTP 400 and nothing is exported. Regression-tested.
  - BUG-3 (tracebacks on bad input): fixed — CLI exits gracefully with a clear
    error (exit 2, no traceback); the web UI returns a readable HTTP 400 page
    for an empty submission. Regression-tested.
  - BUG-4 (demo extractor missed bare 주세요 requests): fixed — patterns now
    cover 주세요/보내주세요-style requests, including the bundled sample.
    Regression-tested.
  - Minor: `demo.py` docstring corrected; model list cached in `client.chat()`.
  - README: AMD's three judging criteria addressed explicitly; problem-size
    statistics added **with sources** (Korea Herald on the 2023 Samsung
    incident; KPMG/University of Melbourne global study 2025; IBM Cost of a
    Data Breach Report 2024); "How we built it" and "Accomplishments" sections
    added; real web-UI screenshots (demo mode, labelled as such) embedded;
    Korean README (`README.ko.md`) added.
  - Test suite: 13 → **22 tests**, all passing (clean-copy run recorded in README).
  - **Round-2 in-repo fixes (applied after the 71/100 re-evaluation):**
    both evaluation reports copied into this repository and this file's
    report references fixed to point at them; the "~700 lines" claim
    corrected to the measured ~480 lines of source (~770 including tests);
    an empty `--file` input now reaches the graceful "document text is
    empty" error (exit 2, no misleading usage message); `ApprovalGate`
    hardened in-process (items copied on construction, approved set
    read-only); one explicit differentiation sentence naming cloud
    alternatives added to both READMEs; "What's next" reordered so the
    expansion logic leads; the hardware kit's `tools/benchmark.py` and
    `tools/sample-long-ko.txt` added to the repo. Test suite: 22 → **26
    tests**, all passing.
  - **Still open (cannot be closed from a repository alone):** a run and
    benchmark on real Lemonade / Ryzen AI hardware, a recorded demo video,
    and validation with real Korean knowledge-worker users.
