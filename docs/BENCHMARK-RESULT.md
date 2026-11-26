# LemonDesk — Benchmark Result (real Lemonade server)

- **Measured at:** 2026-11-26T00:23:04+00:00 (benchmark); CLI verification run 2026-11-26T00:25:22Z
- **Lemonade base URL:** http://localhost:13305/api/v1 (LemonDesk ran in the same runtime as the server)
- **Server reachable (health check):** yes
- **Models reported by server:** Qwen3-4B-GGUF
- **Overall mode:** **real** — every task in every run was served by the real model; zero demo fallbacks

## Environment — read this first

This run used a **free cloud GPU runtime (Google Colab)**, not Ryzen AI hardware:
Lemonade 2026.48.3 served Qwen3-4B-GGUF through its **llamacpp / CUDA** backend on an
**NVIDIA Tesla T4**. It proves the full LemonDesk workflow against a *real* Lemonade
server with a *real* model — the previous "real mode proven only against a fake
server" limitation is closed. It does **not** claim Ryzen AI / NPU performance:
a benchmark on Ryzen AI hardware (ideally the Ryzen AI Max+ 395) is still outstanding
and will be published the same way when it happens.

| Item | Value |
|---|---|
| Environment | Google Colab free GPU runtime (hosted VM) |
| CPU / APU | Colab hosted VM (exact CPU model not exposed); system RAM reported by Lemonade: 12.7 GB |
| GPU actually used | NVIDIA Tesla T4, 15,360 MiB total — **8,279 MiB used** with the model loaded |
| OS | Ubuntu 24.04 (Colab image) |
| Python | 3.13.16 |
| Lemonade version | **2026.48.3** (embeddable build, `lemond`) |
| Backend / recipe | llamacpp / **cuda**; checkpoint `unsloth/Qwen3-4B-GGUF:Q4_0` (2,265.7 MB) |
| Server-side generation speed | **≈ 48–50 tokens/s** (Lemonade/llama.cpp telemetry: tps 47.93 and 50.40 on the CLI run; prompt eval ≈ 1,543 tok/s) |

## Measured results

Per-task latency is LemonDesk's own audit-log measurement for each Lemonade chat
completion (summarize / translate / actions). Output size is in characters —
LemonDesk's client does not receive token usage, so no token figures are reported
or estimated. Produced by `tools/benchmark.py --runs 2` against the live server.

### Bundled sample (examples/sample-ko.txt, 80 chars) — run 1

- Wall-clock total: **44.48 s** | Mode: **real** | Model: `Qwen3-4B-GGUF` | Audit rows: 3
- Output: summary 78 chars, translation 177 chars, action items 2

| Task | Mode | Latency (audit log) |
|---|---|---|
| summarize | real | 26291.3 ms |
| translate | real | 10143.9 ms |
| actions | real | 8039.4 ms |

### Bundled sample — run 2

- Wall-clock total: **34.45 s** | Mode: **real** | Model: `Qwen3-4B-GGUF` | Audit rows: 3
- Output: summary 78 chars, translation 178 chars, action items 2

| Task | Mode | Latency (audit log) |
|---|---|---|
| summarize | real | 13293.8 ms |
| translate | real | 12041.6 ms |
| actions | real | 9109.6 ms |

### Long meeting notes (tools/sample-long-ko.txt, 1,220 chars) — run 1

- Wall-clock total: **58.81 s** | Mode: **real** | Model: `Qwen3-4B-GGUF` | Audit rows: 3
- Output: summary 220 chars, translation 2,601 chars, action items 5

| Task | Mode | Latency (audit log) |
|---|---|---|
| summarize | real | 9270.0 ms |
| translate | real | 20082.5 ms |
| actions | real | 29457.4 ms |

### Long meeting notes — run 2

- Wall-clock total: **66.35 s** | Mode: **real** | Model: `Qwen3-4B-GGUF` | Audit rows: 3
- Output: summary 303 chars, translation 2,789 chars, action items 6

| Task | Mode | Latency (audit log) |
|---|---|---|
| summarize | real | 9871.7 ms |
| translate | real | 21885.5 ms |
| actions | real | 34585.4 ms |

## End-to-end CLI verification (same session)

`lemondesk.cli --file examples/sample-ko.txt --approve A1 --export export.json` in real mode:

- Summary (model output): 회의 보고서를 준비해야 합니다. 금요일까지 검토 보고서를 팀에 보내주세요. 프로젝트 일정은 다음 주 회의에서 공유되며, 마감은 월요일입니다.
- Translation (model output): "A meeting report must be prepared. Send the review report to the team by Friday. The project schedule will be shared at next week's meeting. The deadline is Monday."
- Action items extracted: A1 회의 보고서를 준비해야 합니다. / A2 금요일까지 검토 보고서를 팀에 보내주세요.
- **Approved: 1 | Exported: 1** — exactly the approved item, nothing else.
- Raw evidence in this repo: [evidence/audit-2026-11-26.jsonl](evidence/audit-2026-11-26.jsonl) (3 rows, all `mode: "real"`) and [evidence/export-2026-11-26.json](evidence/export-2026-11-26.json).

## What this run also found (and fixed)

Preparing the first real run exposed two real-server compatibility bugs that no
fake server could have caught — both fixed with regression tests (suite: 29 tests):

1. **Chat timeout.** The client used one 5 s timeout for everything; a real 4B
   model needs far longer to generate a full translation, so slow-but-working
   servers were misread as unavailable (silently triggering the demo fallback).
   Probe and generation timeouts are now separate (5 s / 300 s).
2. **Model-name field.** Current Lemonade builds report models with a
   `model_name` field (older builds used `id`); the client now accepts both.

Also observed in the field: this Lemonade build has no `/health` endpoint
(the client's `/models` liveness fallback covers it), and the Debian package
targets Debian 13 — on Ubuntu 24.04 the embeddable tarball is the working install.
