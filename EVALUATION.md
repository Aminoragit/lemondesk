# LemonDesk — Independent Adversarial Evaluation

- **Target:** AMD Lemonade Developer Challenge entry "LemonDesk" (already submitted 2026-11-25)
- **Evaluator:** Independent adversarial evaluator (not the builder, not the submitter)
- **Date:** 2026-11-25
- **Standard:** `~/workspace/quality-gate/SUBMISSION-QUALITY-CHECKLIST.md` in full, including v2 §5 additions. Rule applied throughout: **no evidence in the artifact = 0; partial evidence = half.**
- **Materials examined:** local project (`project/README.md`, `SUBMISSION.md`, `LICENSE`, `src/lemondesk/*.py`, `tests/test_lemondesk.py`, `examples/sample-ko.txt`); live repo https://github.com/Aminoragit/lemondesk (fetched 2026-11-25); official challenge page https://www.amd.com/en/developer/resources/technical-articles/2026/join-the-lemonade-developer-challenge.html

## VERDICT

| | |
|---|---|
| **Total** | **58 / 100** |
| **Result** | **FAIL** (PASS requires ≥96) |
| **Prior self-score** | 97/100 (in `SUBMISSION.md`) — **overturned**. The self-score granted near-full marks in categories (especially D) whose checklist items the entry demonstrably does not satisfy. |
| **Instant-FAIL triggers** | §4: none proven. §5-3: **one triggered** — no evidence anywhere in the submission package that the official judging criteria were checked and weighted before submission (see §4 below). Score alone (58 < 96) is independently a FAIL. |

The engineering core is real and honestly presented. The failure is a *proof and evidence* failure: no real-hardware run, no demo video, no screenshots, no users, no market numbers, and a stale judge-facing submission file in the live repo.

---

## 1. Executed verification (all run by this evaluator, 2026-11-25)

Clean copy: project copied to `/tmp/lemondesk-eval`, all `__pycache__` removed before running.

| Check | Command / method | Real result |
|---|---|---|
| Test suite | `python3 -m unittest discover -s tests -v` | **13 run, 13 passed, 0 failed** in 0.550s — matches README's claim (13 tests; README says 0.557s, trivial variance) |
| Lemonade probe | `python3 -m lemondesk.cli --check` | `Lemonade at http://localhost:13305/api/v1: NOT REACHABLE (demo mode will be used)`, exit 0 — as README describes |
| CLI demo (KO sample, no approval) | `--file examples/sample-ko.txt` | Demo notice printed; summary + translation prefixed `[DEMO]`; **Approved: 0 \| Exported: 0**; audit file = exactly 3 rows, all `mode: "demo"`, tasks summarize/translate/actions |
| CLI demo (approve A1 + export) | `--approve A1 --export exp.json` | Exported file contains **exactly A1** — gate works on the CLI path |
| Audit log fields | inspected `/tmp/a1.jsonl` | Each row: `timestamp, task, model, mode, prompt_hash` (SHA-256, verified format), `prompt_chars`, `latency_ms` — README's claimed fields all present |
| English document | `process_document(EN_DOC)` via probe script | Mode demo, direction en→ko, 2 action items, 3 audit rows all `demo` — works |
| Zero dependencies | grep of all imports in `src/` + `tests/` | Only stdlib (`argparse, json, sys, re, hashlib, os, time, datetime, urllib, http.server`) + relative imports — claim **TRUE** |
| Default URL / endpoints | `client.py:10` vs AMD's own playbooks (developer.amd.com: "The default OpenAI-compatible API base URL is `http://localhost:13305/api/v1`"; models at `/api/v1/models`; chat at `/api/v1/chat/completions`) | **Correct.** `http://localhost:13305/api/v1`, `GET /models`, `POST /chat/completions`, health probe — all match Lemonade's real API |
| 3 separate Lemonade calls | `workflow.py` `_run_task` ×3 with distinct prompts; fake-server test asserts 3 audit rows | **TRUE** — summarize / translate / actions are three separate chat completions, each audit-logged |

## 2. Claim-by-claim verification (README + AMD form text)

| Claim | Verdict | Evidence |
|---|---|---|
| "0 approvals = 0 exported, test-proven" | **TRUE (CLI/library path)** | My CLI run: Approved 0 → Exported 0. `workflow.py:34-36` `export()` filters by `approved` set. Caveat: server path — see BUG-2 |
| Approval gate is structural, not a prompt | **Mostly TRUE** | `ApprovalGate` is deterministic code (`workflow.py:24-39`); model output never reaches export except through it. Weakened on the web path (BUG-2) and within-process (BUG-6) |
| Audit log per call with timestamp/model/mode/hash/latency | **TRUE** | `audit.py:13-25`; verified in real output rows |
| Demo output always labelled, never presented as real | **TRUE for the no-server case; FALSE in the mixed-failure case** | No-server runs label correctly. Flaky-server run mislabels — BUG-1 |
| Lemonade inside the reasoning loop | **TRUE in code; NEVER EXECUTED against real Lemonade** | Code routes all 3 steps through Lemonade when reachable. Only a fake server (test double, same repo) has ever answered. No real Lemonade server, no Ryzen AI hardware, ever — by the entry's own admission |
| Hypothesis reversal: "Testing the workflow showed the real problem was different" | **UNVERIFIED — no evidence** | README asserts user/workflow testing occurred, yet also states "No external users… are claimed". No interview, tester, or test record exists anywhere in the package. This is an unsupported narrative claim presented as a finding (see §4 warning) |
| "13 tests, all passing (2026-11-25)" | **TRUE** | Independently re-run: 13/13 OK |
| Web UI smoke-tested | **TRUE, with defects** | I ran the server: GET, /process, /export all respond — but empty input crashes the request (BUG-3) and /export is forgeable (BUG-2) |
| MIT open source | **TRUE** | `LICENSE` is full MIT text (© 2026 Seokwon Choi); GitHub detects "MIT License" on the live repo |

## 3. Bugs found (with reproduction)

- **BUG-1 (moderate) — Mixed-mode results are mislabelled as fully "real".** Reproduction: fake Lemonade server that answers summarize/actions but returns HTTP 500 for translate. Result: `mode: "real"`, `demo_notice: None`, `model: m1` — while the translation is actually the demo fallback (`[DEMO] Please 검토 the 보고서…`) and the audit log shows mixed modes (`summarize=real, translate=demo, actions=real`). `workflow.py` decides mode once from the upfront health check and discards each task's actual mode (`summary, _, model = …`). This directly contradicts the form text's "demo output is always marked [DEMO] and is never presented as real model output" at the result level: a judge seeing `Mode: real` with no notice is misled about one third of the output.
- **BUG-2 (moderate) — Web /export gate validates an attacker-supplied item list.** `server.py:48-53`: the items to be gated arrive in a client-controlled hidden form field; the server builds `ApprovalGate(items)` from whatever was POSTed. Reproduction: `POST /export` with `items=[{"id":"X1","text":"FORGED never extracted"}]&approve=X1` (no prior /process call) → `Exported 1 approved item(s)` with the forged text. The gate is re-checked, but against a list the client invented — there is no server-side state binding export to what the model actually extracted. The "structural gate" claim is therefore overstated for the web UI. (Impact is bounded because export is a local JSON echo, not an irreversible external action — but the headline safeguard does not hold as described on this path.)
- **BUG-3 (low) — Unhandled tracebacks on routine bad input.** CLI with empty document → `ValueError` traceback, exit 1 (`cli.py` never catches it). CLI `--approve A99` → `KeyError` traceback after printing results, exit 1. Web `POST /process` with empty text → unhandled exception in `server.py:45`, connection dropped with no HTTP response (curl: HTTP 000), traceback only in the server log. A judge's first fat-finger produces a crash, not an error message.
- **BUG-4 (low) — Demo action extractor misses a common Korean request form.** In the project's own sample, "금요일까지 검토 보고서를 팀에 **보내주세요**" is not extracted: `demo.py` patterns require "해주세요" but the sentence uses "주세요" alone. Of the sample's sentences, the two extracted items are A1 (a genuine task) and A2 "마감은 월요일입니다" (a deadline statement, arguably not an action item), while an explicit request is missed. Demo-mode extraction quality is weaker than the README's confident description.
- **BUG-5 (low, documentation) — Inaccurate run/implementation descriptions.** (a) `demo.py` docstring says summarize takes "first sentence of each of the first 3 paragraphs"; the code takes the first 3 sentences, period. (b) README's run instructions start a real server with `lemonade-server serve` — this command was not verified against Lemonade's actual CLI (AMD documentation uses the `lemonade` CLI / auto-started server); I could not confirm `lemonade-server serve` exists, so the "How to run with real Lemonade" path is unproven at its first command — consistent with it never having been run.
- **BUG-6 (info) — "Structural" gate is single-process only.** Probe: `gate.approved.add("A1")` (public attribute) exports without `approve()`; mutating `gate.items` after construction lets an injected item be approved and exported. Normal for a library trust boundary, but the absolute wording in the form text ("never exported until a human approves") does not acknowledge any boundary.
- **BUG-7 (info) — Inefficient client.** `client.chat()` re-calls `list_models()` on every invocation (3 extra `/models` round-trips per document); `health()` can issue up to 3 requests. Harmless locally, sloppy for a "technical depth" claim.
- **BUG-8 (artifact, judge-facing) — Live `SUBMISSION.md` is stale and self-contradictory.** The public repo's submission pack is titled "Submission Pack (**NOT submitted**)", states "No GitHub repo created, no form submitted", lists GitHub/Discord IDs as blank `<TO FILL>`, and its form text contains `<PASTE GITHUB REPO URL HERE>` — which GitHub renders as an HTML tag, so the Links line in the live file shows **no URL at all**. A judge who opens the repo's second-most-prominent file learns the opposite of the truth. It also still displays the pre-submission self-score of 97/100, which this evaluation overturns.

No fabricated numbers, users, or revenue were found anywhere — the entry's quantitative honesty is genuine, and BUG-8 is staleness, not deception.

## 4. Instant-FAIL conditions — checked one by one

**Checklist §4:**
| Condition | Result |
|---|---|
| Reconstructed/recreated official form used | **Not triggered** — the challenge has no downloadable form; entry is via AMD's own web form (official page, "Fill out the submission form"). No template was recreated |
| Subset font / Hangul loss, no rendering verification | **Not triggered** — no document/PDF artifact; Hangul renders intact in the live repo and in my CLI runs |
| Fabricated numbers / performance / user reactions | **Not proven** — every number in the package (13 tests) re-verified as real. **Warning:** the "Testing the workflow showed…" hypothesis-reversal narrative (§2) is an unverified claim of user testing with zero supporting evidence; if AMD probes it, it reads as invented fieldwork. It is scored 0-evidence under B, not treated as proven fabrication |
| AI decorative but packaged as core | **Not triggered** — Lemonade is genuinely the inference path for all 3 steps in code. Caveat (scored under D, not §4): that path has never run against a real Lemonade server |
| Demo/link broken; mockup presented as real screen | **Not triggered** — repo link opens (verified); demo mode is explicitly labelled, the opposite of a mockup passed off as real. No demo video/screenshot exists at all (scored 0 under D, not a §4 trigger) |

**Checklist §5-3 (v2):**
| Condition | Result |
|---|---|
| LLM-produced numbers/scores presented unverified as final results | **Not triggered** — the model produces no numbers; export is deterministic |
| Irreversible action auto-executed without an approval gate, unexplained | **Not triggered** — no irreversible action exists in the system; export is gated on the CLI path (server path weakness = BUG-2, disclosed here) |
| **Submitted without checking the judging criteria/weights** | **TRIGGERED.** The official page states three criteria (community impact, technical depth & quality, creativity) with no weights. Nothing in `SUBMISSION.md`, the README, or the form text mentions these criteria, maps evidence to them, or shows they were checked pre-submission; "creativity" in particular is never addressed. Per §5-2 B+ and §5-3, this item scores 0 and is an instant-FAIL condition |
| Synthetic/mock data presented as real data | **Not triggered** — demo data is labelled `[DEMO]` everywhere in the no-server path (mixed-mode edge = BUG-1) |
| Estimate-level evidence stated as confirmed fact | **Not triggered, one borderline** — the hypothesis-reversal narrative (above) is the borderline case; everything else is appropriately hedged ("faithful test double", "biggest open weakness") |

## 5. Checklist scoring — every line item, with evidence

### A. Form compliance — 14 / 20 (self-score claimed 20)
| Item | Pts | Evidence |
|---|---|---|
| Official form used as-is; no recreation (5) | 5 | Web-form-only entry per official page; paste-ready text prepared for the official project-details field (`SUBMISSION.md`) |
| Form items/order/titles pixel-identical to original (5) | 2.5 | No downloadable template exists, so pixel comparison is impossible and none was performed; the adapted standard (exact field + complete fields) is only half-met because the *live repo copy* of the form text is defective (BUG-8: placeholder, blank IDs) |
| No missing required items; format conditions met (4) | 2 | Form text itself is complete, but: no demo/work link beyond run-it-yourself commands, and the repo artifact a judge actually reads omits the repo URL (rendered invisible) and both IDs |
| No font breakage; Hangul verified by render + re-extraction (3) | 3 | Hangul verified intact in live GitHub rendering and in my own CLI executions on the Korean sample |
| Signature/date/eligibility/deadline conditions match the notice (3) | 1.5 | Deadline ("until supplies exhausted") and membership are as the official page states, but eligibility documentation is contradictory and unresolved in the package: the form's own footnote (US/Canada residency) vs the entrant's assertion that Koreans are eligible — the package records only the assertion, no AMD confirmation. Half credit |

### B. Idea / problem definition — 5.5 / 15 (self-score claimed 14)
| Item | Pts | Evidence |
|---|---|---|
| Concrete Inspiration opening from personal anecdote / field scene (4) | 2 | README opens with a concrete but *generic third-person* scene ("A Korean knowledge worker receives…"). No personal anecdote, no named person, no field moment. Half |
| Problem size proven with market/statistics numbers (4) | **0** | Zero statistics anywhere in README or form text — no market size, no document-volume, no cloud-privacy incident, nothing. The self-score conceded this yet deducted only 1 point *in total* for B |
| One-sentence differentiation from existing alternatives (4) | 2 | The local-vs-cloud difference is clear across paragraphs, but no single sentence names or contrasts a concrete alternative (ChatGPT/DeepL/etc.). Half |
| Hypothesis verification/reversal process shown (3) | 1.5 | A reversal is *asserted* ("people need a better translator" → local+accountable loop) but the discovery process has no evidence — no users, interviews, or experiments exist in the package. Half, generously |
| §5-2 B+: judging criteria/weights checked on official page and evidence concentrated on the largest item | **0 (folded)** | See §4 §5-3 trigger. No mention of AMD's three criteria anywhere in the submission package |

### C. Logic / architecture — 17 / 20 (self-score claimed 20)
| Item | Pts | Evidence |
|---|---|---|
| Pipeline traceable step-by-step, input → processing → output (5) | 5 | README diagram + `workflow.py` — document → 3 task calls → gate → export; verified by execution |
| AI/technology roles separated and named per system (5) | 5 | Summarize / translate / extract are separate named calls with task-specific prompts (`workflow.py:17-21`) |
| Constraint engineering explicit — what the model cannot do, who decides, why (5) | 5 | Boundary declaration in README and `workflow.py:7-9`: model never decides export; deterministic code + human decide; reason (accountability for wrong extractions) stated |
| Failed approach vs adopted approach contrast + breakthrough (3) | **0** | Absent. The demo fallback is a contingency, not a failed first approach; no iteration narrative exists in README or form text |
| Built With / full tech stack (2) | 2 | README "Built with" lists Lemonade endpoints + stdlib modules; verified accurate (zero deps confirmed) |
| §5-2 C+ (all four folded in, all required for full marks) | ✓✓✓△ | Boundary sentence ✓; structural (non-prompt) approval gate ✓ on CLI path, △ on server path (BUG-2); independent verification step ✓ (fake-server test double — separate code, though same author/repo, so independence is partial); audit log on every AI call ✓ (`audit.py`, verified in outputs). The △ is absorbed in the deductions above rather than zeroing C |

### D. Execution / proof — 5 / 20 (self-score claimed 18 — the largest inflation)
| Item | Pts | Evidence |
|---|---|---|
| Real release/deployment proof — release date, store/live URL, working demo (5) | 2.5 | A public GitHub repo exists and opens (verified live: public, 11 commits, MIT detected). But there is no deployed/live demo, no release/tag, and the app has never run in its real mode anywhere. Half |
| ≥3 types of verifiable quantitative results (5) | 2.5 | Exactly **one** type exists: test count (13, real). No users, no time saved, no accuracy, no benchmark, no tokens/sec. Audit rows contain latency values but no performance results are published. Half at best |
| Real user reactions / quotes / field activity evidence (4) | **0** | README explicitly: "No external users or revenue are claimed." No quotes, no testers, no field activity |
| Real transaction (money/payment/subscription) working end-to-end (3) | **0** | No transaction of any kind exists in the system; export is a local file write |
| Demo video / screenshots that are real screens, not mockups (3) | **0** | None exist — no video, no screenshot, no image anywhere in the repo. The official page explicitly gives "bonus points for recorded demos"; the entry has none |
| §5-2 D+: proof includes an evaluation metric / test-case count / calibration figure | ✓ (folded) | Test-case count (13) present — the only D+ satisfied; reproducibility ✓ (deterministic demo, identical outputs re-run by me); sponsor technology inside the loop ✓ in code, ✗ never executed against the real sponsor technology |

### E. Narrative / completeness — 11.5 / 15 (self-score claimed 15)
| Item | Pts | Evidence |
|---|---|---|
| All sections of the expected structure filled, 0 empty (4) | 2 | README deviates from the canonical structure: there is **no "How we built it"** (replaced by "How Lemonade is used") and **no "Accomplishments that we're proud of" section at all**. Half |
| Challenges honest and specific, solved/unsolved distinguished (3) | 3 | Genuinely strong: real-hardware gap named "biggest open weakness", demo weakness, model-dependence, no-users — all disclosed |
| What We Learned is project-specific, not generic (3) | 3 | "LLM proposes / deterministic code disposes / human approves / everything is logged" — specific and earned |
| What's Next closes with expansion logic to a bigger market (3) | 1.5 | First half is a feature list (benchmark, .docx, installer, export targets); only the final sentence generalises the pattern. Half |
| One-line definition (tagline) memorable and accurate (2) | 2 | "Paste a Korean or English work document… nothing is exported until a human approves it" — accurate and distinctive |
| §5-2 E+: weaknesses disclosed ✓; "what we chose not to build" stated ✓ | ✓ | Both present ("Named audience" section lists deliberate exclusions) — E is the entry's most honest category |

### F. Pre-submit verification — 5 / 10 (self-score claimed 10)
| Item | Pts | Evidence |
|---|---|---|
| Every link click-verified — demo, video, repo, docs all open (3) | 1.5 | Repo link opens (I verified). There are no demo/video links to verify, and the form's pasted repo URL cannot be re-verified post-submission from the package; the repo-internal copy of that URL is broken-by-rendering (BUG-8). Half |
| Zero typos/broken images/empty attachments; files actually attached (3) | 1.5 | Code files all present and consistent local↔live, but the live `SUBMISSION.md` is stale ("NOT submitted", blank IDs, invisible placeholder) — a glaring artifact defect that a pre-submit pass should have caught. Half |
| Adversarial review performed ≥1× and all findings fixed (2) | 1 | A self-review iteration log is claimed (94→97) but it was self-scoring by the builder, and it missed BUG-1…BUG-8, several of which are trivially findable. This independent review is the first adversarial one — and it post-dates submission. Half |
| Deadline/eligibility/submission channel re-confirmed against the official notice (2) | 1 | Channel and period match the official page, but the eligibility conflict (form footnote vs entrant assertion) was resolved by assertion, not by documentary confirmation from AMD. Half |

### Category totals
| Category | This evaluation | Self-score | Δ |
|---|---|---|---|
| A. Form | 14 / 20 | 20 | −6 |
| B. Idea | 5.5 / 15 | 14 | −8.5 |
| C. Logic | 17 / 20 | 20 | −3 |
| D. Execution/proof | 5 / 20 | 18 | −13 |
| E. Narrative | 11.5 / 15 | 15 | −3.5 |
| F. Verification | 5 / 10 | 10 | −5 |
| **Total** | **58 / 100 — FAIL** | 97 | **−39** |

## 6. Judged against AMD's own criteria (official page)

The official page judges on **community impact, technical depth & quality, creativity**, requires an **open-source license**, AMD AI Developer Program membership, and gives bonus points for recorded demos/work links. It publishes **no weights**.

- **Open source (hard requirement): PASS, cleanly.** Public repo, GitHub-detected MIT license, complete source + tests. This is the entry's one unqualified pass.
- **Community impact: WEAK.** Clear documentation, zero-dependency reproducibility, and a bilingual niche are genuinely community-friendly. But impact is entirely hypothetical: 0 stars, 0 forks, 0 users, no blog post, no video, no evidenced Discord (#AMDDevChallenge) participation, no Korean-language README for the very community it names. Nothing has reached a community yet.
- **Technical depth & quality: MODERATE-LOW.** The architecture is well-reasoned (gate, audit, honest fallback, independent test double) and the code is clean — but the whole system is ~600 lines of stdlib wrapping three chat-completion calls. It uses none of Lemonade's distinguishing capabilities (no NPU/GPU backend awareness, no model management, no performance evaluation — one of AMD's own suggested submission types), and its real mode has literally never executed against Lemonade. BUG-1/2/3 further undercut the "quality" claim for the two headline safeguards.
- **Creativity: LOW-MODERATE.** Summarize + translate + extract is the single most generic LLM workflow in existence. The approval-gate/audit framing and the KO↔EN internal-document angle are a real twist, but a twist on a commodity workflow, with no demo to make it vivid.
- **Competitiveness for 30 laptops (until supplies exhausted): WEAK / bottom-quartile as it stands.** The pool is first-come and quality-judged ("if we love it"). Rival entries visible in the ecosystem (e.g. multi-component systems actually run and filmed on local hardware, with demo videos and performance data) outgun this entry on every stated criterion except documentation honesty. An evaluator at AMD who clones the repo gets a well-written README, a demo-mode toy translator, and a submission file telling them the project was never submitted. The two cheapest fixes (real-hardware run + recorded demo) are precisely the two AMD explicitly rewards, and both are missing.

**Weakest points, honestly ranked:** (1) never run on real Lemonade / Ryzen AI hardware — the entry's core claim is unexecuted; (2) no demo video or screenshot of any kind, despite explicit bonus points; (3) no external users, reactions, or community footprint of any kind; (4) stale, self-contradicting `SUBMISSION.md` in the live repo; (5) no problem-size evidence (zero statistics); (6) headline safeguards have real holes (BUG-1, BUG-2); (7) creativity — a generic workflow.

## 7. Prioritised fix list (post-submission; the repo is live and editable)

1. **Run it on real Lemonade and publish the proof.** Install Lemonade on any Ryzen AI (or any supported) machine, run all three tasks in real mode, and add to the README: model name, hardware, tokens/sec and per-task latency from the audit log, plus a terminal screenshot. This single fix attacks D1, D2, technical depth, and the entry's biggest disclosed weakness simultaneously. Also verify/fix the `lemonade-server serve` instruction (BUG-5b) against the real CLI while doing it.
2. **Record a 2–3 minute demo video** (real Lemonade run: document in → summary/translation/items → approve → export, showing the audit log), link it at the top of the README, and post it in Lemonade Discord #AMDDevChallenge with the repo link (also the first real community-impact evidence). AMD explicitly gives bonus points for recorded demos.
3. **Fix or remove the live `SUBMISSION.md` today.** Replace the stale pack with a submitted-state version (real repo URL, IDs filled, status corrected, this evaluation's score rather than the inflated 97) — or delete the file from the repo. Every hour it stays, it contradicts the submission.
4. **Fix BUG-1** (propagate per-task mode; if any task fell back, the result must say so and show the notice), **BUG-2** (bind /export to server-side state from /process, e.g. a server-held session/token, instead of trusting POSTed items), **BUG-3** (catch `ValueError`/`KeyError` in CLI and server; return a clean error and HTTP 400). Add regression tests for all three and update the test count honestly.
5. **Add real screenshots** of the web UI in real mode to the README (post-fix #1), replacing the current zero-image state.
6. **Give B a body:** add problem-size numbers (e.g. share of Korean office work that is bilingual, cloud-AI data-leak incidents/policy bans in Korean firms — cited, not invented) and recruit 2–3 real Korean knowledge workers to run it and quote their reactions verbatim. This converts the currently *asserted* hypothesis reversal into evidence — or replaces it with what testers actually said.
7. **Fix the demo extractor** (add bare "주세요" and related request patterns — BUG-4), correct the `demo.py` docstring (BUG-5a), and cache the model list in `client.chat()` (BUG-7).
8. **Address AMD's criteria explicitly in the README:** a short "Why this matters to the Lemonade community" section (community impact), a Korean-language README version for the named audience, and one creative extension (e.g. a second workflow — meeting-notes → bilingual minutes) to lift the creativity score above "generic trio".
9. **Resolve the eligibility paper trail:** keep AMD's written confirmation of Korean eligibility (if obtained) in the package; if it does not exist in writing, obtain it via ai_dev_program@amd.com and file it — F/A credit depends on documents, not assertions.

*End of evaluation. No project code or repo files were modified by this evaluation; all probes ran against a disposable copy in /tmp.*
