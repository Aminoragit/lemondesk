# LemonDesk — Independent Adversarial Re-Evaluation (Round 3)

- **Target:** AMD Lemonade Developer Challenge entry "LemonDesk" (submitted 2026-11-25)
- **Evaluator:** Independent adversarial evaluator (round 3; not the builder, not the submitter, not the remediator)
- **Date:** 2026-11-26
- **Standard:** `~/workspace/quality-gate/SUBMISSION-QUALITY-CHECKLIST.md` in full, including v2 §5. Rule: **no evidence = 0; partial evidence = half.**
- **Round 1:** 58/100 FAIL (`EVALUATION.md`). **Round 2:** 71/100 FAIL (`EVALUATION-2.md`). This round re-scores the current state after the 2026-11-26 changes: a real end-to-end run against a real Lemonade server, two real-server compatibility fixes (29 tests), real-mode UI screenshots, and a narrated demo video published with release v0.3.0.
- **Materials examined:** local project (all source, tests, both READMEs, `SUBMISSION.md`, `docs/BENCHMARK-RESULT.md`, all three evidence files, all six screenshots, the demo video file itself — probed and frame-sampled); live repo https://github.com/Aminoragit/lemondesk (main page, releases list, v0.3.0 tag page, expanded-assets endpoint, live `docs/BENCHMARK-RESULT.md`).

## VERDICT

| | |
|---|---|
| **Total** | **81.5 / 100** |
| **Result** | **FAIL** (PASS requires ≥96) |
| **Round 2** | 71/100 — this round recovered **+10.5**, almost all of it in D (execution proof, +4.5) and F (verification hygiene, +2.5) |
| **Instant-FAIL triggers** | §4: **none**. §5-3: **none** (see §4). The score alone (81.5 < 96) is independently a FAIL |
| **Where the remaining 18.5 points live** | Real users (D3, 4 pts — still zero), transactions (D4, 3 pts — structurally unreachable for this product), the eligibility paper trail (A5/F4, ~2.5 pts), the still-generic opening scene (B1, 2 pts), the unvalidated hypothesis (B4, 1.5 pts), and the fact that the real run happened on an NVIDIA cloud GPU, not on AMD's own Ryzen AI platform (D1/D2 remainders) |

The headline change is real and it matters: **the entry's central claim — inference on real Lemonade — has now been executed, measured, and evidenced.** The run is framed with unusual honesty (cloud GPU, CUDA backend, explicitly *not* a Ryzen AI benchmark), its numbers are internally consistent to the centisecond, and it found two genuine compatibility bugs that no fake server could have caught. What has not changed at all: no human other than its author has ever used it, and the eligibility file is still an assertion.

---

## 1. Executed verification (all run by this evaluator, 2026-11-26)

Clean copy: project copied to `/tmp/lemondesk-eval3`, all `__pycache__` removed before running.

| Check | Method | Real result |
|---|---|---|
| Test suite | `python3 -m unittest discover -s tests` on clean copy | **29 run, 29 passed, 0 failed** in 3.372s (README says 4.289s — timing is environment-dependent; the count, which is the claim that matters, is exact) |
| Chat-timeout fix | code inspection + suite | `client.py`: `chat_timeout: float = 300.0`, stored and actually used in the chat POST (`timeout=self.chat_timeout`); probe timeout remains separate. Regression tests for the split are in the suite and pass |
| `model_name` fix | code inspection + suite | `client.py` model parsing: `m.get("id") or m.get("model_name") or m.get("name") or str(m)` — accepts both old and current Lemonade shapes |
| Empty-file probe (round-2 nit) | `lemondesk.cli --file /tmp/empty.txt` | **FIXED.** Exit 2, stderr `Error: document text is empty. Provide a non-empty document.` — no traceback, no misleading usage message |
| BUG-6 probe (round-2 residual) | constructed `ApprovalGate`, then mutated the caller's original list (appended forged item, edited item text), tried `gate.approved.add(...)`, exported with/without `approve()` | **FIXED.** Caller's-list mutations have no effect (export after `approve("A1")` returns the original unmutated text; `approve("X1")` → `KeyError`); `approved` returns a `frozenset` (`.add` → `AttributeError`); zero approvals export `[]`. Residual-by-design note: Python name-mangled privates remain reachable to deliberate in-process introspection — true of any Python encapsulation, and no claim depends on more than this |
| Line-count claim | `wc -l src/lemondesk/*.py` = **492**; including tests = **829** | README's "~490 lines of source, ~830 including the test suite" is **accurate** (round-2's "~700 lines" nit is closed) |
| Benchmark internal consistency | arithmetic on `docs/BENCHMARK-RESULT.md` | **All four wall-clock totals equal the sum of their three per-task latencies** (44.4746→44.48s; 34.4450→34.45s; 58.8099→58.81s; 66.3426→66.35s). Output sizes, item counts, and modes are coherent across runs |
| CLI audit evidence | `docs/evidence/audit-2026-11-26.jsonl` | 3 rows, all `mode: "real"`, model `Qwen3-4B-GGUF`, timestamps 2026-11-26T00:25:22–00:25:39Z — matching the document's stated CLI verification run; latency sum 31.6s is consistent with a ~32s end-to-end run |
| UI audit evidence | `docs/evidence/ui-audit-2026-11-26.jsonl` | 3 rows, all `real`, timestamps 01:04:00–01:04:17Z, consistent with the real-mode UI capture session |
| Export evidence | `docs/evidence/export-2026-11-26.json` | Exactly one item, `A1` "회의 보고서를 준비해야 합니다." — matches the CLI verification narrative exactly |
| Real-mode screenshots | visual inspection of `05-real-result.png`, `06-real-export.png` | **Genuine real-mode captures.** Result screen shows `Mode: real \| Model: Qwen3-4B-GGUF`, a genuinely model-written summary (paraphrased, unlike the demo's extractive output), a real translation, and **4** action items with approval checkboxes — exactly as the README describes, including its note that model output varies run to run. Export screen: "Exported 1 approved item(s)" with exactly A1. Hangul intact everywhere |
| Demo video (local file) | `ffprobe` + frame extraction at 50s and 90s | Duration **98.056s = 1m38s** as claimed; H.264 video + AAC audio (narration track present). Frame at 50s: the real export capture with the caption "Only the human-approved item is exported". Frame at 90s: closing card with repo URL and "29 automated tests". The video is a narrated assembly of real captures/outputs — and the README describes it in exactly those terms, no more |
| Demo video (live asset) | GitHub `releases/expanded_assets/v0.3.0` + `sha256sum` of the local file | The v0.3.0 release asset (2.21 MB, uploaded 2026-11-26T01:16:06Z) has sha256 `fd326525…f78d`, **identical to the local `lemondesk-demo.mp4`** — the published asset is byte-for-byte the video I inspected |
| Live repo | opened main page, releases list, v0.3.0 page, live benchmark doc | Public, MIT detected, **27 commits, 3 releases** (v0.1.0 / v0.2.0 / v0.3.0), **0 stars, 0 forks**. Live README content matches local, with all eight images (demo + real-mode captures) rendering; live `docs/BENCHMARK-RESULT.md` is identical to the local file |
| Eligibility paper trail | full-text search of the project for eligibility/residency material | **Still assertion-only.** The only mentions of eligibility anywhere in the package are in the two evaluation reports themselves. No AMD written confirmation exists in the repo or package |
| Opening scene | README Inspiration, first paragraph | **Still the generic third-person scene** ("A Korean knowledge worker receives…"). Nothing personal was added — and, to the entry's credit, nothing was fabricated either |

**One evidence-preservation gap found:** `tools/benchmark.py` writes its audit log into a `tempfile.TemporaryDirectory()` that is deleted when the script exits. The benchmark table's per-task latencies are therefore **not backed by raw audit rows preserved anywhere** — the preserved JSONL files cover the CLI and UI runs, not the four benchmark runs. The numbers pass every internal-consistency check I can apply (wall-clock = Σ latencies on all four runs, plausible tok/s, coherent outputs), and I found no sign of invention; but under this checklist's standard, the benchmark's raw evidence chain is one link shorter than the CLI run's. Recorded as an (a)-list fix, not a fabrication concern.

## 2. Round-2 residual items — re-checked

| Round-2 item | Status in round 3 |
|---|---|
| BUG-6 (in-process gate mutation) | **CLOSED** — see §1 probe. Items copied on construction, `approved` is a read-only `frozenset`, forged-ID approval raises `KeyError` |
| Empty-`--file` misleading message | **CLOSED** — graceful "document text is empty", exit 2 |
| "~700 lines" overstatement | **CLOSED** — now "~490 / ~830", measured 492 / 829 |
| Dead `../EVALUATION.md` reference in `SUBMISSION.md` | **CLOSED** — both reports now live in the repo and `SUBMISSION.md` links to them in-repo; verified in the live root listing |
| One-sentence differentiation naming alternatives | **CLOSED** — "Unlike pasting the document into a cloud chatbot or translation service (ChatGPT- or DeepL-class tools), LemonDesk never sends the document anywhere…" |
| What's Next ordering | **CLOSED** — expansion logic now leads the section |
| Release/tag artefact | **CLOSED, exceeded** — three dated releases, the latest carrying the demo-video asset |
| Personal opening scene (B1) | **STILL OPEN** — generic scene, unchanged; correctly not fabricated. Requires the author's own true material |
| Eligibility paper trail (A5/F4) | **STILL OPEN** — assertion-only; no AMD document filed; the fix still starts with an email to ai_dev_program@amd.com |
| Real Lemonade run + benchmark (round-2 §7b-1) | **CLOSED IN SUBSTANCE, OPEN IN PLATFORM** — real server, real model, published benchmark with raw evidence for the CLI/UI runs. But the hardware was an NVIDIA Tesla T4 in a cloud runtime via CUDA — the sponsor's own Ryzen AI / NPU path remains unexecuted and unmeasured |
| Recorded demo video (round-2 §7b-2) | **CLOSED as a video** — narrated 1m38s, built from real captures, published as a release asset, linked from the README, cloud-GPU disclosure on-screen and in text. **Open half:** no evidence of the second half of that item — posting to Lemonade Discord #AMDDevChallenge; nothing in the repo evidences any Discord/community presence |
| Real Korean testers (round-2 §7b-3) | **STILL OPEN** — README still states plainly: "No Korean knowledge worker has yet run LemonDesk and reacted to it" |
| Community footprint (round-2 §7b-4) | **STILL ZERO measured** — 0 stars, 0 forks, 0 external users (live repo, checked this round) |
| Transactions (round-2 §7b-5) | Unchanged — structurally unreachable by design; checklist misfit, not a target |

## 3. Claim-by-claim verification of what changed since round 2

| Claim (as presented for this round) | Verdict | Evidence |
|---|---|---|
| Real end-to-end run vs a REAL Lemonade server (2026.48.3, Qwen3-4B-GGUF, llamacpp/CUDA, Tesla T4, Colab) on 2026-11-26 | **TRUE** | Two independent audit JSONL files (CLI + UI sessions) with real-mode rows, timestamps, model name, and plausible latencies; genuine real-mode UI captures whose model summary visibly differs from the deterministic demo output; benchmark doc's environment table names the exact stack |
| Benchmark: 2 docs × 2 runs, all mode=real | **TRUE as reported; raw rows not preserved** | Table is internally consistent to ±0.01s on all four runs (§1); but `benchmark.py` discards its audit log (temp dir), so the four runs' raw rows exist nowhere — the claim rests on the table plus the preserved CLI/UI evidence |
| Server telemetry ≈48–50 tok/s | **PLAUSIBLE, attributed, not independently verifiable from the repo** | Stated as Lemonade/llama.cpp telemetry (tps 47.93 / 50.40 on the CLI run) and framed as a range; consistent with the CLI run's output volume and latencies. The server log itself is not in the repo, so this is a quoted measurement, not a preserved artefact |
| The run does NOT claim Ryzen AI/NPU performance | **TRUE — framing is exemplary** | The benchmark doc's second section is a bolded environment disclosure ("not Ryzen AI hardware… does not claim Ryzen AI / NPU performance"); the README repeats the caveat in the benchmark section, in Challenges, in the criteria section, and in both release notes |
| CLI approval/export verified in real mode | **TRUE** | Export evidence file contains exactly A1; the UI export capture shows the same; CLI audit rows bracket the run |
| Two compatibility bugs found by the run and fixed (300s chat timeout; `model_name`) | **TRUE** | Both fixes present in `client.py` and exercised by regression tests in the 29-test suite, which I re-ran clean |
| Test suite now 29 | **TRUE** | My clean-copy run: 29 run, 29 OK |
| Real-mode screenshots 04–06 added | **TRUE** | Inspected 05 and 06 visually (§1); all three render on the live repo |
| Narrated demo video (1m38s) published as v0.3.0 release asset | **TRUE** | Duration 98.056s; AAC narration stream; live asset sha256 identical to the inspected local file; README link resolves to the release |
| BUG-6 residual | **CLOSED** | §1 probe |
| Personal opening scene | **UNCHANGED, honestly so** | Still generic; no invented anecdote |
| Eligibility paper trail | **UNCHANGED** | Assertion-only; no AMD document in package or repo |

No fabricated numbers, users, reactions, or hardware claims were found in round 3 either. The entry's quantitative honesty remains its most consistent property across three rounds.

## 4. Instant-FAIL conditions — re-checked one by one

**Checklist §4:**
| Condition | Result |
|---|---|
| Reconstructed official form | **Not triggered** — web-form entry via AMD's own form; nothing recreated |
| Subset font / Hangul loss | **Not triggered** — Hangul verified intact in live rendering, in the new real-mode screenshots (visually inspected), in the video frames, and in my own executions |
| Fabricated numbers / performance / user reactions | **Not triggered** — 29/29 tests re-run by me; benchmark arithmetic verified; tok/s explicitly attributed to server telemetry and stated as a range; no user reactions claimed anywhere |
| AI decorative but packaged as core | **Not triggered — and the round-1/2 caveat is now lifted.** Lemonade was genuinely the inference path for all 3 steps *in code*; as of 2026-11-26 it is also executed fact against a real Lemonade server, with audit evidence |
| Demo/link broken; mockup as real screen | **Not triggered** — repo, releases, benchmark doc, and video asset all open and verified live; real-mode captures are genuine screens, demo captures remain labelled demo |

**Checklist §5-3 (v2):**
| Condition | Result |
|---|---|
| LLM-produced numbers presented unverified | **Not triggered** — the model produces no numbers; benchmark numbers come from the audit log and server telemetry, both identified as such |
| Irreversible action without approval gate | **Not triggered** — the gate now holds on CLI, library, web, *and* in-process-mutation probing (§1) |
| Submitted without checking judging criteria/weights | **Not triggered** — cleared in round 2; the criteria section remains and now carries the real-run evidence |
| Synthetic/mock data presented as real | **Not triggered** — demo artefacts labelled; the real run is framed as a cloud-GPU run in the benchmark doc, both READMEs, the video, and the release notes. This is the opposite of the failure mode |
| Estimate-level evidence stated as fact | **Not triggered** — the one soft number (≈48–50 tok/s) is attributed to named telemetry readings and hedged as a range; the hypothesis remains labelled a design bet |

## 5. Checklist scoring — round 3 vs round 2

### A. Form compliance — 17 / 20 (round 2: 16.5)
| Item | Pts | Evidence |
|---|---|---|
| Official form used as-is; no recreation (5) | 5 | Unchanged |
| Form items/completeness vs original (5) | 4 | Unchanged reasoning: the judge-facing repo record is complete and accurate; the submitted form text itself is frozen at its round-1 state — disclosed, not repairable |
| No missing required items; format conditions (4) | 3.5 | Improved: a demo video and dated releases are now reachable from the submitted repo link, closing the "no demo/work link beyond run-it-yourself" gap in substance. Withheld 0.5: the form AMD received still contains only the bare repo URL — everything else depends on the judge following it |
| No font breakage; Hangul verified (3) | 3 | Re-verified incl. new captures and video frames |
| Signature/date/eligibility/deadline conditions (3) | 1.5 | **Unchanged.** Eligibility still rests on the entrant's assertion; no AMD written confirmation exists in the package or repo (§1) |

### B. Idea / problem definition — 11 / 15 (round 2: 9.5)
| Item | Pts | Evidence |
|---|---|---|
| Personal anecdote / field scene opening (4) | 2 | **Unchanged.** Generic third-person scene; no named person, no personal moment — and no fabrication. Half |
| Problem size proven with statistics (4) | 4 | Unchanged; all three verified at source in round 2 |
| One-sentence differentiation vs alternatives (4) | 3.5 | **Fixed in substance.** A single explicit sentence now names the alternatives (ChatGPT-/DeepL-class cloud tools) and states the difference (nothing leaves the machine; nothing exported without approval). Withheld 0.5: it sits mid-paragraph inside a long Inspiration rather than standing as the crisp one-liner the criterion envisions |
| Hypothesis verification/reversal process (3) | 1.5 | **Unchanged.** The real run validates technical feasibility, not the user hypothesis; the text still honestly labels it an unvalidated design bet with user validation "explicitly still to do". Half |
| §5-2 B+: judging criteria checked, evidence concentrated | ✓ (folded) | Criteria section now backs its technical-depth claim with the real-run benchmark |

### C. Logic / architecture — 19 / 20 (round 2: 18.5)
| Item | Pts | Evidence |
|---|---|---|
| Pipeline traceable step-by-step (5) | 5 | Unchanged; now also executed end-to-end against a real server |
| AI roles separated and named (5) | 5 | Unchanged |
| Constraint engineering explicit (5) | 5 | The gate the boundary declaration describes now holds on every path probed across three rounds, including in-process mutation (§1) |
| Failed approach vs adopted approach contrast (3) | 2 | **Strengthened.** Beyond the round-2 safeguard contrasts, the real run produced two genuine field-found failures with adopted fixes (5s chat timeout → separate 300s generation timeout; `id`-only model parsing → `model_name` support), documented in the benchmark doc. Still safeguard/compatibility-level rather than a product-level pivot, so not full |
| Built With / full stack (2) | 2 | Unchanged and accurate |
| §5-2 C+ (four additions) | ✓✓✓✓ | Boundary sentence ✓; structural gate ✓ (all paths + in-process); independent verification ✓ (fake-server double + three rounds of independent adversarial evaluation); audit log on every call ✓ (real-run rows preserved for CLI/UI sessions) |

### D. Execution / proof — 11 / 20 (round 2: 6.5)
| Item | Pts | Evidence |
|---|---|---|
| Real release/deployment proof (5) | 4 | **Materially improved.** Three dated GitHub releases; the app has run in real mode end-to-end against a real Lemonade server with a published benchmark; a demo video exists. Withheld 1: no live hosted demo a judge can click and use, and the real run was on cloud NVIDIA hardware, not the challenge's Ryzen AI platform |
| ≥3 types of verifiable quantitative results (5) | 4 | **Materially improved.** Now at least four project-owned types: test-case count (29, re-verified), per-task latencies (12 measurements, 2 docs × 2 runs × 3 tasks — internally consistent), server generation speed (≈48–50 tok/s, telemetry-attributed), and resource/wall-clock figures (VRAM 8,279 MiB, run totals). Withheld 1: the benchmark runs' raw audit rows were not preserved (temp-dir audit log), tok/s rests on quoted telemetry rather than a preserved server log, and there is still no accuracy/quality metric |
| Real user reactions / field evidence (4) | **0** | **Unchanged.** README: "there are no external users yet, and we claim none" |
| Real transaction end-to-end (3) | **0** | **Unchanged.** No transaction exists in the system (by design — §7 note) |
| Demo video / screenshots that are real (3) | 3 | **Fixed.** Real-mode screenshots verified genuine (`Mode: real` on screen, model-written outputs, gate flow); narrated 1m38s video verified as a real artefact — published asset is byte-identical (sha256) to the file I probed and frame-sampled; built from real captures and described in exactly those terms |
| §5-2 D+ | ✓ (folded) | Test-case count ✓; reproducibility ✓ (deterministic demo; benchmark script + inputs in-repo); sponsor technology inside the loop ✓ **and now executed against the real sponsor technology** — the round-2 ✗ is closed |

### E. Narrative / completeness — 14.5 / 15 (round 2: 13.5)
| Item | Pts | Evidence |
|---|---|---|
| All sections of the expected structure filled (4) | 4 | Unchanged; benchmark + real-mode capture sections added without displacing the canonical set |
| Challenges honest and specific (3) | 3 | Now also discloses the cloud-GPU-vs-Ryzen framing of its own headline result — the entry applies its honesty standard to its best news, not just its failures |
| What We Learned project-specific (3) | 3 | Unchanged |
| What's Next closes with expansion logic (3) | 2.5 | **Improved.** The section now leads with the expansion logic (the pattern generalising to contracts/HR/tickets) and demotes the feature list to support. Withheld 0.5: the section's final sentence is still the feature list, so it opens with expansion more than it *closes* with it |
| Tagline memorable and accurate (2) | 2 | Unchanged |
| §5-2 E+ | ✓ | Weaknesses disclosed ✓ (now including the platform caveat on the real run); "what we chose not to build" stated ✓ |

### F. Pre-submit verification — 9 / 10 (round 2: 6.5)
| Item | Pts | Evidence |
|---|---|---|
| Every link click-verified (3) | 3 | **Fixed.** I opened the repo, all three releases, the v0.3.0 page, the live benchmark doc, and the asset endpoint this round; every README image (demo + real-mode) renders live; the video link resolves to a real, hash-verified asset |
| Zero broken artifacts; files actually present (3) | 3 | **Fixed.** Round 2's two defects are both closed and re-verified: the evaluation references resolve in-repo, and the line-count claim now matches measurement (492/829 vs "~490/~830") |
| Adversarial review performed and findings fixed (2) | 2 | **Fixed.** Three independent rounds now; every code finding from rounds 1–2 (BUG-1…8, the empty-file nit, BUG-6) is fixed, regression-tested, and re-probed by me in this round rather than taken on trust. The reviews still post-date the original submission — inherent to remediation, and disclosed as such |
| Deadline/eligibility/channel re-confirmed vs official notice (2) | 1 | **Unchanged.** Channel/period fine; eligibility remains assertion-only with no AMD document. Half |

### Category totals
| Category | Round 3 | Round 2 | Round 1 | Δ (R3−R2) |
|---|---|---|---|---|
| A. Form | 17 / 20 | 16.5 | 14 | +0.5 |
| B. Idea | 11 / 15 | 9.5 | 5.5 | +1.5 |
| C. Logic | 19 / 20 | 18.5 | 17 | +0.5 |
| D. Execution/proof | 11 / 20 | 6.5 | 5 | +4.5 |
| E. Narrative | 14.5 / 15 | 13.5 | 11.5 | +1 |
| F. Verification | 9 / 10 | 6.5 | 5 | +2.5 |
| **Total** | **81.5 / 100 — FAIL** | 71 | 58 | **+10.5** |

## 6. Judged against AMD's own criteria (round 3)

- **Open source (hard requirement): PASS, cleanly** — unchanged; public repo, GitHub-detected MIT, three tagged releases.
- **Community impact: still potential-only, now with artefacts to point at.** The entry now has the things a community could actually consume — releases, a narrated demo video, a published benchmark — but measured impact remains zero: 0 stars, 0 forks, 0 external users, and no evidenced presence in Lemonade Discord #AMDDevChallenge (the challenge's own participation channel). The README continues to say exactly this about users.
- **Technical depth & quality: materially improved — the quality half is now strong, the depth half still modest.** Quality is argued with the strongest artefact set this entry has ever had: 29 tests, a real-server run with internally consistent measurements, two field-found compatibility bugs fixed and regression-locked, and three rounds of independent probing that the code has survived. Depth is still bounded: ~490 lines of stdlib wrapping three chat completions, no use of Lemonade's distinguishing capabilities (no NPU path, no model management, no backend awareness), and the one real run used the CUDA backend on NVIDIA hardware — competent use of the sponsor's *software*, not yet of the sponsor's *hardware*.
- **Creativity: low-moderate, unchanged.** The accountability reframing remains the idea; the real run and video make it vivid but do not extend it.
- **Competitiveness for 30 laptops: now mid-pack credible, still short of the front.** The two proofs AMD explicitly rewards — work actually run on the platform and a recorded demo — both exist for the first time. What front-runners will still have over this entry: runs on Ryzen AI / Strix Halo hardware itself, and any sign of other humans using or reacting to the thing. An AMD evaluator who clones the repo today gets a working, honestly-benchmarked Lemonade app with a video — a categorically different artefact from round 1's well-written README wrapped around an unexecuted claim.

## 7. Remaining deductions — split by what can close them

### (a) Fixable in-repo now (concrete; ≈ +2–3 points available)
1. **Preserve the benchmark runs' raw audit rows.** `tools/benchmark.py` writes its audit log to a `TemporaryDirectory` and deletes it; change it to write `benchmark-audit.jsonl` next to the result file, and commit the existing runs' successor evidence on the next run. The script change is in-repo today; regenerating the evidence needs any live Lemonade server (the Colab path already proven works). (D2 remainder)
2. **Personal opening scene.** Still the generic scene. Editable in-repo *only if* the author supplies one true personal scene; inventing one would be fabrication. (B1, author-supplied — unchanged from round 2)
3. **Eligibility paper trail.** The repo-side filing is trivial once a document exists; the actionable step is the email to ai_dev_program@amd.com requesting written confirmation of Korean eligibility, then filing the reply in the repo and referencing it from `SUBMISSION.md`. (A5/F4 — depends on AMD replying, but nothing else is missing)
4. **Post the Discord artefact.** The demo video + repo link in Lemonade Discord #AMDDevChallenge is an action, not an edit — but it is doable today and is the only remaining zero-cost community step; any response it draws becomes the first community evidence. (Community impact; no checklist points until someone reacts)
5. **Optional tidy:** the README's remediation paragraph narrates "the suite is now at 26 tests" mid-history before updating to 29 — chronologically framed and accurate, but a skim-reading judge could misread it; a one-line reorder removes the ambiguity. (Cosmetic; no points scored against it this round)

*Not fixable at all:* the submitted AMD form text is frozen (13 tests, no criteria mapping, no stats, bare repo URL). The repo record mitigates by preserving and annotating it; no further action exists.

### (b) Only fixable with Ryzen AI hardware, real users, or third parties (≈ +15 points locked here)
1. **A run on AMD's own platform** — Lemonade on Ryzen AI (ideally the Ryzen AI Max+ 395 / Strix Halo, or any XDNA2 NPU / Radeon ROCm path), with the same benchmark published the same way. This is the single largest remaining technical-depth item: every real-mode number the entry owns was produced on a competitor's GPU through CUDA. (D1 remainder, D2 remainder, AMD technical depth)
2. **Real Korean knowledge-worker testers (2–3)** running it on their own documents, quoted verbatim. Converts the labelled design bet into evidence — or replaces it with what testers actually said. (B4, D3 — 5.5 points between them)
3. **Any measured community footprint** — Discord participation with responses, external stars/forks/users, a write-up by someone other than the author. (Community impact; supports D3)
4. **D4 (transactions, 3 pts) remains structurally unreachable** for this product — there is no payment/subscription surface and adding one would distort it. Recorded, as in round 2, as a checklist misfit rather than a remediation target. With D4 excluded, the realistic ceiling after perfect execution of (b)1–3 is roughly **93–96** — this entry can now plausibly reach the low end of that band, which it could not in round 2.

*End of re-evaluation. No project code or repo files were modified by this evaluation; all probes ran against a disposable copy in /tmp, live-repo checks were read-only, and the video was inspected from the local file whose sha256 matches the published release asset.*
