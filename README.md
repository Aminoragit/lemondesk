# LemonDesk — Local-first Korean–English AI work assistant powered by AMD Lemonade

> Paste a Korean or English work document. Get a summary, a KO↔EN translation, and extracted action items — all inferred **locally** by AMD Lemonade, and nothing is exported until a human approves it.

## Inspiration

A Korean knowledge worker receives an internal meeting document and wants three things AI is good at — a summary, an English translation for a global teammate, and the action items. The obvious tools are cloud AIs, and the obvious problem is the document itself: internal documents are exactly the ones that should not be pasted into a cloud service. The hypothesis we started with was "people need a better translator." Testing the workflow showed the real problem was different: people need the *whole* summarise–translate–extract loop to run **on their own machine**, and they need a guarantee that machine-extracted tasks do not silently become exported work items. LemonDesk is built around those two findings.

## Named audience

**Korean knowledge workers who cannot send internal documents to cloud AI** — employees handling internal reports, meeting notes, and bilingual (KO/EN) work documents on their own PCs. Deliberately out of scope (what we chose *not* to build): a cloud sync service, automatic sending/posting of action items anywhere, and a general chatbot. Focus over feature count.

## What it does

1. **Detects Lemonade** — probes the Lemonade health endpoint and `GET /api/v1/models`, lists available models (`--check`).
2. **Processes a document** (CLI or web UI) — summary, KO→EN or EN→KO translation (direction auto-detected), and extracted action items.
3. **Human approval gate** — action items are displayed but **not exported** until a human approves specific item IDs. Export is deterministic code behind the gate, never a model decision.
4. **Audit log** — every model call is appended to a JSONL audit log: timestamp, model, mode (`real`/`demo`), SHA-256 prompt hash (not the prompt text), and latency.

## How Lemonade is used — inside the reasoning loop, not as decoration

Lemonade is the inference engine for all three reasoning steps. When a server is reachable, **each step is a separate Lemonade chat completion** (`POST /api/v1/chat/completions`, OpenAI-compatible) with its own task-specific prompt, and each call is audit-logged before its output is used:

```
document ─► [Lemonade chat: summarize] ─► summary
         ─► [Lemonade chat: translate] ─► translation
         ─► [Lemonade chat: extract]   ─► action items ─► ApprovalGate (human) ─► export (approved only)
every call ─► audit.jsonl (timestamp, model, mode, prompt hash, latency)
```

**Boundary declaration: the model never decides what gets exported.** The model may *propose* action items; only deterministic code (`ApprovalGate.export()`) releases items, and only those a human approved. Test-proven: 0 approvals = 0 exported items.

**Verification, independent of the generator:** the test suite runs the workflow against a *separate fake Lemonade server* (a test double implementing the same OpenAI-compatible endpoints) and asserts the outputs, model name, mode, and exactly 3 audit rows — the producer and the checker are different code.

## Demo / offline mode (honest labelling)

If no Lemonade server is detected, LemonDesk runs in a clearly labelled **DEMO/OFFLINE mode**: a deterministic local fallback (extractive summary, fixed-glossary translation, marker-based action extraction). Every demo output is prefixed `[DEMO]`, the CLI/UI prints "NOT real Lemonade/model output", and audit rows record `mode: "demo"`. Demo output is never presented as model output. This exists so reviewers can reproduce the full workflow — including the approval gate and audit log — on any machine, and get identical results (the fallback is deterministic; tests assert this).

## How to run

Requirements: Python 3.10+ only. **Zero third-party dependencies** (standard library only).

```bash
# With a real Lemonade server (https://lemonade-server.ai) running locally:
lemonade-server serve            # default: http://localhost:13305/api/v1
export PYTHONPATH=src
python3 -m lemondesk.cli --check                       # detect server + list models
python3 -m lemondesk.cli --file examples/sample-ko.txt # real inference when reachable

# Demo mode (no server needed — output is labelled DEMO):
python3 -m lemondesk.cli --file examples/sample-ko.txt

# Approve + export (human step — only approved IDs are exported):
python3 -m lemondesk.cli --file examples/sample-ko.txt --approve A1 --export approved.json

# Web UI:
python3 -m lemondesk.server --port 8765                # http://127.0.0.1:8765

# Custom Lemonade address:
LEMONADE_BASE_URL=http://localhost:13305/api/v1 python3 -m lemondesk.cli --check
```

## Tests — real results

```bash
python3 -m unittest discover -s tests -v
# Ran 13 tests in 0.557s — OK  (measured 2026-11-25, Python 3.12.3)
```

13 tests cover: demo determinism and labelling, KO/EN language detection, KO+EN action extraction, approval gate (0 approvals → 0 exported; partial approval; unknown ID rejected), audit log contents/hash/mode validation, health+models against a fake Lemonade server, the full workflow in real mode (3 audit rows, all `real`), offline fallback labelling, and empty-document rejection. A live CLI demo run and a web-UI smoke test were also executed on 2026-11-25: server check correctly reported "NOT REACHABLE", the demo run produced 3 audit rows (`mode: "demo"`), and approving only `A1` exported exactly 1 item.

## Challenges / limitations — disclosed, not hidden

- **Not yet run against real Lemonade hardware in this build environment.** The build machine had no Lemonade server (the `--check` probe confirms this above), so real-mode behaviour is proven against a faithful fake server implementing Lemonade's OpenAI-compatible endpoints, not against a physical Ryzen AI machine. This is the project's biggest open weakness.
- **Demo translation is intentionally weak** — a 10-word fixed glossary with `[DEMO-untranslated]` markers. It demonstrates the pipeline, not translation quality. Real translation quality depends entirely on the Lemonade-served model.
- **Action-item extraction quality is model-dependent** in real mode; the approval gate exists precisely because extracted items can be wrong — a human remains accountable for what gets exported.
- **No external users or revenue are claimed.** Proof offered is small and real: 13 passing automated tests, a reproducible deterministic demo, and a verified audit trail — nothing synthetic is presented as real usage.
- Single-user, local files only; no multi-user auth, no document formats beyond UTF-8 plain text in this version.

## What we learned

Local inference changes the privacy conversation only if the *workflow around it* is also local and accountable: an unaudited local model is still a black box. Splitting the system into "LLM proposes / deterministic code disposes / human approves / everything is logged" made the local story actually trustworthy — and made the whole thing testable without a GPU.

## What's next

Run and benchmark on a real Ryzen AI Max+ 395 machine (tokens/sec and latency per task, published honestly), add .docx/.md input, a one-click installer that detects/installs Lemonade, and export targets (Markdown checklist, calendar) that remain behind the same approval gate. The larger step: the same local-first, approval-gated pattern generalises to other sensitive bilingual office work — contracts, HR documents, support tickets — where "never leaves this machine" is the feature.

## Built with

- **AMD Lemonade** — local inference server, OpenAI-compatible API (`/api/v1/chat/completions`, `/api/v1/models`, health) — the reasoning engine for all three tasks
- **Python 3 standard library only** — `urllib`, `http.server`, `hashlib`, `unittest` (zero third-party dependencies)
- HTML form UI served by the stdlib server (no framework)

## License

MIT — see [LICENSE](LICENSE).
