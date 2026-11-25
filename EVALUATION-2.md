# LemonDesk — Independent Adversarial Re-Evaluation (Round 2)

- **Target:** AMD Lemonade Developer Challenge entry "LemonDesk" (submitted 2026-11-25)
- **Evaluator:** Independent adversarial evaluator (round 2; not the builder, not the submitter, not the remediator)
- **Date:** 2026-11-25
- **Standard:** `~/workspace/quality-gate/SUBMISSION-QUALITY-CHECKLIST.md` in full, including v2 §5. Rule: **no evidence = 0; partial evidence = half.**
- **Round 1:** 58/100 FAIL (`EVALUATION.md`). This round re-scores the **current** state after remediation: bugs 1–4 fixed with regression tests (22 tests), `SUBMISSION.md` rewritten, README criteria section + cited statistics + How-we-built-it + Accomplishments + real screenshots, Korean README, live repo at 15 commits.
- **Materials examined:** local project (all source, tests, both READMEs, `SUBMISSION.md`, screenshots); live repo https://github.com/Aminoragit/lemondesk (blob-SHA comparison, see §1); official challenge page (re-fetched this round); the three cited statistic sources (each opened and checked this round).

## VERDICT

| | |
|---|---|
| **Total** | **71 / 100** |
| **Result** | **FAIL** (PASS requires ≥96) |
| **Round 1** | 58/100 — remediation recovered **+13**, concentrated in B (statistics), E (structure), A/F (artifact hygiene) |
| **Instant-FAIL triggers** | §4: **none**. §5-3: **none** — the round-1 trigger (judging criteria never checked) is **cleared** by the README's explicit criteria section. The score alone (71 < 96) is independently a FAIL |
| **Where the remaining 29 points live** | Almost all in D (execution proof, 6.5/20): no real-hardware run, no demo video, no users, no transactions. These are no longer fixable by editing text — see §7 split |

The remediation is genuine: every claimed bug fix survived independent re-probing (§2), every new statistic verified against its source (§3), and the live repo is byte-identical to the local project (§1). What remains is the same core truth as round 1, now smaller: **the entry's central claim — inference on real Lemonade — has still never been executed, and no human other than its author has ever used it.**

---

## 1. Executed verification (all run by this evaluator, 2026-11-25)

Clean copy: project copied to `/tmp/lemondesk-eval2`, all `__pycache__` removed before running.

| Check | Method | Real result |
|---|---|---|
| Test suite | `python3 -m unittest discover -s tests -v` on clean copy | **22 run, 22 passed, 0 failed** in 3.089s (README says 1.572s — timing is environment-dependent; the count, which is the claim that matters, is exact) |
| Live ↔ local identity | `git hash-object` locally vs GitHub blob SHAs via connector `get_file_contents`, 12 files (both READMEs, SUBMISSION, 5 changed source files, tests, 3 PNGs) | **12/12 blob SHAs identical.** Live repo = local project, byte for byte. Commit count 15 confirmed via API, including the 4 remediation commits |
| Lemonade probe | `python3 -m lemondesk.cli --check` | `NOT REACHABLE`, exit 0 — as documented |
| CLI demo (KO sample, no approval) | `--file examples/sample-ko.txt` | Demo notice; **Approved: 0 \| Exported: 0**; exactly 3 audit rows, all `demo`, all claimed fields present; A2 is now the 보내주세요 sentence (BUG-4 fix visible in real output) |
| CLI approve + export | `--approve A2 --export` | Export file contains **exactly A2** with the correct Korean text |
| Zero dependencies | import scan of `src/` + `tests/` | Stdlib + relative imports only — **TRUE** |
| Screenshots | `file` + visual inspection of `02-result.png` | Real PNGs, 1100×1050. The result screen is the genuine web UI: DEMO notice on screen, Hangul intact (no font breakage), A1/A2/A3 with A2 = 보내주세요 item, export checkboxes. **Real captures of demo mode, labelled as demo mode — not mockups, not passed off as real-mode** |
| Korean README | read in full | Complete mirror of the English README (all sections incl. criteria, stats, remediation disclosure), not a stub |
| Official page | re-fetched this round | Criteria unchanged: community impact / technical depth & quality / creativity, no weights; open-source required; "Bonus points for recorded demos or links to work" |

## 2. Round-1 adversarial probes — re-run against the remediated code

| Probe | Round 1 result | Round 2 result |
|---|---|---|
| **Mixed mode** (flaky server) | `mode: "real"`, no notice, demo output unmarked at result level | **FIXED, verified twice.** The remediation's own regression test fails *translate*; I independently probed with a server failing a *different* task (*actions*): result `mode: "mixed"`, `task_modes {summarize: real, translate: real, actions: demo}`, notice present and naming the fallen-back task, audit modes exactly equal to `task_modes` |
| **Forged web export** (POST items + approve, no prior process) | Forged item `X1` exported | **FIXED.** Fresh server: export-before-process → **HTTP 400, nothing exported**. After a real `/process`: approving a forged ID → **400**; a mixed valid+forged approval set → **400, nothing exported** (no partial leak); a client-POSTed `items` field is ignored — approving A1 exports the *server-side* Korean text, not client text. Duplicate approval of A1 exports exactly one A1; zero approvals export `[]` |
| **Empty inputs** | CLI tracebacks (exit 1); web POST dropped connection (HTTP 000) | **FIXED.** CLI empty `--text` → `Error: document text is empty…`, exit 2, no traceback. Unknown `--approve A99` → clear error, exit 2, nothing exported. Missing file → clear error, exit 2. Web empty `/process` → readable **HTTP 400** page. One nit: an empty *file* (`--file empty.txt`) exits 2 via the argparse path with the misleading message "provide --file or --text" instead of "document text is empty" — graceful, but the message is wrong (see §7a) |
| **Demo extractor** (BUG-4) | Sample's 보내주세요 request missed | **FIXED.** Sample now extracts 3 items; A2 is "금요일까지 검토 보고서를 팀에 보내주세요." (A3 "마감은 월요일입니다" remains a deadline statement counted as an item — a quality quirk of marker-based extraction, disclosed in the README's limitations) |
| **Model-list caching** (BUG-7) | `/models` re-listed per chat call | **FIXED** in code (`client.py` `_cached_models`) and by the remediation's counting-server test, which passed in my clean run |
| **`demo.py` docstring** (BUG-5a) | Misdescribed summarize | **FIXED** — docstring now matches the code (first 3 sentences) |
| **Run instructions** (BUG-5b) | Unverified `lemonade-server serve` command | **FIXED by removal** — README now defers to https://lemonade-server.ai for install/start and states only the verified default API address |
| **In-process gate boundary** (BUG-6, info) | `gate.approved.add(...)` / mutating `gate.items` bypasses `approve()` | **STILL PRESENT** (my re-probe: both mutations export). This is a library trust boundary — the same process that owns the gate can mutate it — and no claim in the remediated README depends on in-process adversaries. Recorded as a residual nit (§7a), not a regression |
| **Stale `SUBMISSION.md`** (BUG-8) | "NOT submitted", blank IDs, invisible placeholder URL, 97/100 | **FIXED.** Live file is now a Submission Record: SUBMITTED 2026-11-25, AMD confirmation quoted, real repo URL, GitHub `Aminoragit` / Discord `aminora.` filled, the historical form text preserved *as* a historical record (with its at-the-time-accurate "13 tests" explicitly annotated), the 58/100 round-1 verdict recorded, remediation itemised. One defect remains: it points to `../EVALUATION.md`, which is **not in the repo** — from the repo root that path escapes the repository, so a judge following it hits a dead reference (§7a) |

## 3. New-evidence verification (statistics added in remediation)

All three statistics were opened at their cited sources this round:

| Statistic as stated in README | Source check | Verdict |
|---|---|---|
| 2023 Samsung engineers uploaded source code + meeting minutes to ChatGPT; restriction from 1 May 2023; in-house translation/summarisation tools | *The Korea Herald* article 3118116 (opened): confirms all elements, incl. "meeting minutes and source codes", "banned temporarily from May 1", in-house tools for "translation and the summarizing of documents" | **TRUE, accurately cited** |
| 48% of AI-using employees uploaded sensitive company/customer info to public gen-AI tools; 32,352 workers, 47 countries (KPMG / U. Melbourne 2025) | TechXplore/Gillespie et al. (opened): "surveyed 32,352 employees in 47 countries"; "Nearly half (48%) of employees have uploaded sensitive company or customer information into public generative AI tools" | **TRUE, accurately cited** |
| Global average data-breach cost USD 4.88M, 604 organisations (IBM 2024) | IBM report page (opened): "global average breach hit a record USD 4.88 million"; "70% of the 604 organizations studied" | **TRUE, accurately cited** |

No fabricated numbers were found in round 2 either. One quantitative nit: the criteria section calls the system "~700 lines of stdlib Python". Source under `src/` totals **459 lines**; ~700 (708) is only reached by including the 249-line test file. As written it overstates the codebase it describes (§7a).

## 4. Instant-FAIL conditions — re-checked one by one

**Checklist §4:**
| Condition | Result |
|---|---|
| Reconstructed official form | **Not triggered** — web-form entry via AMD's own form; nothing recreated |
| Subset font / Hangul loss | **Not triggered** — Hangul verified intact in live rendering, in screenshots (visually inspected), and in my own executions |
| Fabricated numbers / performance / user reactions | **Not triggered** — 22/22 tests re-run by me; all 3 new statistics verified at source (§3); no user reactions claimed anywhere. The "~700 lines" phrasing is an overstatement-by-inclusion (tests counted), scored as a nit, not fabrication |
| AI decorative but packaged as core | **Not triggered** — Lemonade remains the genuine inference path for all 3 steps in code. Standing caveat (scored in D): that path has still never run against a real Lemonade server |
| Demo/link broken; mockup as real screen | **Not triggered** — repo opens; all 12 checked files live; screenshots are real captures, explicitly labelled demo mode |

**Checklist §5-3 (v2):**
| Condition | Result |
|---|---|
| LLM-produced numbers presented unverified | **Not triggered** |
| Irreversible action without approval gate | **Not triggered** — the gate now holds on CLI, library, *and* web paths under forged-input probing (§2) |
| Submitted without checking judging criteria/weights | **NO LONGER TRIGGERED.** Round 1's trigger is cleared at the entry level: README §"Judged on AMD's criteria" addresses all three stated criteria with evidence and honest limits; `SUBMISSION.md` records them. Honest caveat: this mapping was added *post-submission* — the frozen form text itself still does not address the criteria; the repo (which the form links to) now does |
| Synthetic/mock data presented as real | **Not triggered** — demo data and demo screenshots are labelled everywhere, including in the screenshot section heading |
| Estimate-level evidence stated as fact | **Not triggered** — the round-1 borderline (asserted "hypothesis reversal") has been *removed as a finding* and relabelled "a design bet, not a user-research finding" in both READMEs. This is the correct remediation |

## 5. Checklist scoring — every category, round 2 vs round 1

### A. Form compliance — 16.5 / 20 (round 1: 14)
| Item | Pts | Evidence |
|---|---|---|
| Official form used as-is; no recreation (5) | 5 | AMD web form; paste-text approach unchanged |
| Form items/completeness vs original (5) | 4 | The judge-facing repo copy is now complete and accurate: submitted status, real URL (link line renders), both IDs filled. Withheld 1: the *submitted form text itself* is frozen at its round-1 state (13 tests, no criteria mapping) — disclosed honestly in `SUBMISSION.md`, but the form AMD received cannot be retro-improved |
| No missing required items; format conditions (4) | 3 | URL + IDs now present in the repo record; screenshots + run instructions give a work link. Still no demo video/live demo link (also scored in D) |
| No font breakage; Hangul verified (3) | 3 | Verified in live repo, screenshots, and executions |
| Signature/date/eligibility/deadline conditions (3) | 1.5 | **Unchanged.** Period/channel match the official page, but the eligibility paper trail is still assertion-only: no AMD written confirmation exists in the package or repo. Half credit, as round 1 |

### B. Idea / problem definition — 9.5 / 15 (round 1: 5.5)
| Item | Pts | Evidence |
|---|---|---|
| Personal anecdote / field scene opening (4) | 2 | **Unchanged.** Still a generic third-person scene ("A Korean knowledge worker receives…"); no named person, no personal moment. Half |
| Problem size proven with statistics (4) | 4 | **Fixed.** Three statistics, each opened and verified at its source this round (§3): Samsung 2023 leak + ban, 48% / 32,352 workers / 47 countries, IBM USD 4.88M / 604 orgs |
| One-sentence differentiation vs alternatives (4) | 2 | Improved context ("the open-source, runs-on-your-own-PC version of that answer" vs Samsung's in-house response and the cloud route) but still no single sentence naming and contrasting a concrete alternative product. Half |
| Hypothesis verification/reversal process (3) | 1.5 | The reversal narrative remains, now honestly labelled an unvalidated **design bet** with user validation "explicitly still to do". Honesty is correct and prevents any fabrication concern, but the item rewards *evidence of verification*, and there is still none — no users, interviews, or experiments. Half |
| §5-2 B+: judging criteria checked, evidence concentrated | ✓ (folded) | Criteria section now exists and maps evidence per criterion — the round-1 zero is cleared |

### C. Logic / architecture — 18.5 / 20 (round 1: 17)
| Item | Pts | Evidence |
|---|---|---|
| Pipeline traceable step-by-step (5) | 5 | Unchanged; re-verified by execution |
| AI roles separated and named (5) | 5 | Unchanged; three task-specific calls |
| Constraint engineering explicit (5) | 5 | Boundary declaration unchanged, and the gate it describes now actually holds on every path I could probe (§2) |
| Failed approach vs adopted approach contrast (3) | 1.5 | **Now present, at half strength.** The remediation cycle is documented in both READMEs and `SUBMISSION.md`: the original design's claims (pure-real labelling, client-trusted export) failed adversarial probing and were replaced by per-task mode derivation and server-side state, locked in by regression tests. It is a genuine failed-vs-adopted contrast — but about safeguard design, not a product-level first approach (cf. Omnnia's pipeline pivot), so half |
| Built With / full stack (2) | 2 | Unchanged and accurate |
| §5-2 C+ (four additions) | ✓✓✓✓ | Boundary sentence ✓; structural gate ✓ (now incl. web path); independent verification ✓ (fake-server double + two rounds of independent adversarial evaluation, the second confirming the first's fixes); audit log on every call ✓ (re-verified, modes consistent with results even in mixed runs) |

### D. Execution / proof — 6.5 / 20 (round 1: 5)
| Item | Pts | Evidence |
|---|---|---|
| Real release/deployment proof (5) | 2.5 | Public repo (15 commits, blob-verified live), runnable deterministic demo, real screenshots. Still: no deployed/live demo, no release or tag, and the app has **never run in real mode anywhere**. Half |
| ≥3 types of verifiable quantitative results (5) | 2.5 | Still essentially one project-owned type: test-case count (22, real). The cited statistics quantify the *problem*, not the *project's* performance; audit latencies exist but no benchmark results are published; no accuracy, time-saved, tokens/sec, or user counts. Half |
| Real user reactions / field evidence (4) | **0** | **Unchanged.** README: "there are no external users yet, and we claim none" |
| Real transaction end-to-end (3) | **0** | **Unchanged.** No transaction of any kind exists in the system (by design — see §7 note) |
| Demo video / screenshots that are real (3) | 1.5 | **Half fixed.** Screenshots: real captures, visually verified by me, honestly labelled demo mode. Video: still none, despite the official page's explicit bonus points for recorded demos |
| §5-2 D+ | △ (folded) | Test-case count ✓; reproducibility ✓ (deterministic demo, identical outputs across my runs); sponsor technology in the loop ✓ in code, **✗ still never executed against real Lemonade** |

### E. Narrative / completeness — 13.5 / 15 (round 1: 11.5)
| Item | Pts | Evidence |
|---|---|---|
| All sections of the expected structure filled (4) | 4 | **Fixed.** README now carries the full canonical set: Inspiration → What it does → How we built it → Challenges → Accomplishments → What we learned → What's next → Built With, plus criteria/stats/screenshots sections; zero empty sections. Korean mirror is equally complete |
| Challenges honest and specific (3) | 3 | Stronger than round 1: discloses the 58/100 FAIL, the four bugs, the unvalidated hypothesis, and the hardware gap, in both languages |
| What We Learned project-specific (3) | 3 | Unchanged, specific |
| What's Next closes with expansion logic (3) | 1.5 | **Unchanged text** — feature list first, generalisation only in the final sentence. Half |
| Tagline memorable and accurate (2) | 2 | Unchanged |
| §5-2 E+ | ✓ | Weaknesses disclosed ✓; "what we chose not to build" stated ✓ |

### F. Pre-submit verification — 6.5 / 10 (round 1: 5)
| Item | Pts | Evidence |
|---|---|---|
| Every link click-verified (3) | 2 | Repo opens; all screenshot images present and rendering (blob-verified + visually inspected); all three statistic source URLs opened by me this round and resolve to the cited content. Withheld 1: no demo/video link exists to verify, and one repo-internal reference is dead (next item) |
| Zero broken artifacts; files actually present (3) | 2 | Live `SUBMISSION.md` defect (round-1's worst artifact flaw) is fixed; 12/12 files blob-identical live↔local. Withheld 1: `SUBMISSION.md` references `../EVALUATION.md`, which is **not in the repo** — a dead pointer for any judge; plus the "~700 lines" overstatement (§3) |
| Adversarial review performed and findings fixed (2) | 1.5 | **Substantially fixed.** A genuine independent adversarial review (round 1) was performed and its code findings (BUG-1…5, 7, 8) are fixed and regression-tested — re-verified by probing in round 2, not taken on trust. Withheld 0.5: BUG-6 (info) remains, and the review still post-dates the original submission (inherent to remediation) |
| Deadline/eligibility/channel re-confirmed vs official notice (2) | 1 | **Unchanged.** Channel and period re-confirmed against the official page this round; eligibility still rests on the entrant's assertion with no AMD document in the package. Half |

### Category totals
| Category | Round 2 | Round 1 | Δ |
|---|---|---|---|
| A. Form | 16.5 / 20 | 14 | +2.5 |
| B. Idea | 9.5 / 15 | 5.5 | +4 |
| C. Logic | 18.5 / 20 | 17 | +1.5 |
| D. Execution/proof | 6.5 / 20 | 5 | +1.5 |
| E. Narrative | 13.5 / 15 | 11.5 | +2 |
| F. Verification | 6.5 / 10 | 5 | +1.5 |
| **Total** | **71 / 100 — FAIL** | 58 | **+13** |

## 6. Judged against AMD's own criteria (round 2)

- **Open source (hard requirement): PASS, cleanly** — unchanged; public repo, GitHub-detected MIT.
- **Community impact: still weak, now honestly framed.** Bilingual docs, zero-dependency reproducibility, deterministic demo, and a criteria section that speaks AMD's language are real documentation improvements. Measured impact remains zero: 0 stars, 0 forks, 0 users, no video, no evidenced Discord #AMDDevChallenge presence. The README now says exactly this.
- **Technical depth & quality: improved to moderate.** The quality half is now genuinely argued with artefacts: 22 tests, a remediation cycle where every externally found bug was reproduced, fixed, and regression-locked — and which survived my independent re-probing, including a mixed-mode probe on a task the remediation's own test didn't cover. The depth half is unchanged: ~460 lines of stdlib wrapping three chat calls, no use of Lemonade's distinguishing capabilities, and **real mode still never executed against Lemonade or Ryzen AI hardware**.
- **Creativity: low-moderate, now argued explicitly.** The criteria section makes the best honest case (accountability reframing, mixed mode, KO↔EN angle). The underlying workflow remains the generic trio; no new creative extension was built.
- **Competitiveness for 30 laptops: still below the bar, less far below.** The repo no longer sabotages itself (round 1's stale `SUBMISSION.md` was the single most damaging artefact, and it is fixed). But AMD's two explicitly rewarded proofs — a recorded demo and work actually run on the platform — are still both absent, and rival entries that run and film on real hardware still outgun this one on every stated criterion except documentation honesty.

## 7. Remaining deductions — split by what can close them

### (a) Fixable in-repo now (concrete; ≈ +4–5 points available)
1. **Dead evaluation reference.** `SUBMISSION.md` points to `../EVALUATION.md`, which is not in the repo. Copy `EVALUATION.md` (and this report) into the repo (e.g. `docs/evaluations/`) and fix the paths. (F2)
2. **"~700 lines" overstatement.** `src/` is 459 lines; ~700 includes tests. Correct to "~460 lines of source (~700 including the test suite)" in both READMEs. (F2 honesty nit)
3. **Empty-file CLI message.** `--file empty.txt` exits 2 via argparse with "provide --file or --text" — the file *was* provided; route empty content to the same graceful `ValueError` message as `--text`, and add a regression test. (BUG-3 residue)
4. **BUG-6 residual (info).** Make `ApprovalGate` defensive in-process: copy `items` on construction and keep `approved` private behind a read-only view, so the "structural" wording is airtight even inside the process. Add a mutation test.
5. **One-sentence differentiation.** Add a single explicit sentence naming the alternatives, e.g. in Inspiration: unlike pasting the document into a cloud chatbot (ChatGPT/DeepL-class tools), nothing leaves the machine. (B3)
6. **What's Next closing.** Reorder so the expansion logic (sensitive bilingual office work) leads and the feature list supports it, instead of the reverse. (E4)
7. **Release/tag.** Cut a `v0.1.0` GitHub Release from the current main — a small, real deployment artefact. (D1, partial)
8. **Personal opening scene.** The Inspiration opening can be rewritten in-repo *if* the entrant supplies one true personal scene; inventing one would be fabrication, so this needs the author's own material, not an editor's. (B1, author-supplied)
9. **Eligibility paper trail.** If any AMD reply confirming Korean eligibility exists, file it in the repo and reference it from `SUBMISSION.md`; if none exists, the fix starts with an email to ai_dev_program@amd.com — the repo part (filing it) is trivial once the document exists. (A5/F4)

*Not fixable at all:* the submitted AMD form text is frozen (13 tests, no criteria mapping, no stats). The repo record already mitigates this by preserving and annotating it; no further action exists.

### (b) Only fixable with physical hardware, a real-run video, or real users (≈ +20 points locked here)
1. **Real Lemonade / Ryzen AI run + published benchmark** — model name, hardware, tokens/sec and per-task latency from the audit log, terminal/UI captures of *real* mode. Closes the entry's biggest disclosed weakness; lifts D1, D2, and AMD's technical-depth judgement simultaneously.
2. **Recorded demo video of a real run** (2–3 min: document in → summary/translation/items → approve → export → audit log), linked at the top of the README and posted to Lemonade Discord #AMDDevChallenge. The official page explicitly awards bonus points for this; also the first real community-impact artefact (D5 remainder, community impact).
3. **Real Korean knowledge-worker testers (2–3)** running it on their own documents, quoted verbatim. Converts the labelled design bet into evidence — or replaces it with what testers actually said (B4, D3).
4. **Any measured community footprint** — Discord participation, a blog write-up, external stars/forks/users. Community impact is currently potential-only by the entry's own admission.
5. **D4 (transactions, 3 pts) is structurally unreachable** for this product: there is no payment/subscription surface and adding one would distort it. Recorded for completeness — these 3 points should be treated as a checklist misfit for this entry, not a remediation target. Even a perfect execution of (b)1–4 leaves the realistic ceiling near ~93–96, which is itself an honest statement about how far a no-hardware, no-user entry can go under this checklist.

*End of re-evaluation. No project code or repo files were modified; all probes ran against a disposable copy in /tmp, and live-repo checks were read-only.*
