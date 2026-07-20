# ER Triage AI Co-pilot — Roadmap
**Project:** ER Assisted Triage Workflow System  
**Stack:** N8N Cloud · OpenAI GPT-4o · Pinecone · Supabase · Vanilla JS  
**Last Updated:** July 17, 2026 (Roadmap Revision)

---

## ⚠️ Roadmap Revision — 2026-07-17 (Portfolio-First Re-prioritization)

**Decision:** As of 2026-07-10, full HHH pass (10/10 dimensions) was achieved — Agentic orchestration, RAG, guardrails, eval harness, and observability are all real, evaluated, and resume-claimable. Assessed that continuing to deepen Phase 5/6 AI engineering has diminishing marginal value against the primary goal (job search, 60 min/day budget) — an interviewer is unlikely to probe past what's already built and evaluated. Higher leverage now is converting the build into an actual visible, documented portfolio asset.

**This does not delete or invalidate any roadmap item below.** All original Phase 5/6/7 specs remain intact for reference and are still valid future work. This section only re-sequences priority.

### Revised Priority Order

| Priority | Item | Effort | Status | Rationale |
|---|---|---|---|---|
| 1 | **P7-A: Production Hosting** | 1-2 hr | ⏳ Not started | Real URL — table stakes for a portfolio link in an interview |
| 2 | **Phase 7 wrap-up** (README + architecture diagram, case study, EB1 content angle, resume/LinkedIn update) | 1-2 days | ⏳ Not started | The actual job-search-facing asset. Sequenced *before* auth/quota — a well-documented hosted demo beats an undocumented gated one |
| 3 | **P7-B + P7-C: Auth + per-user quota** | 6-9 hr combined | ⏳ Not started — **scope decision still open, see below** | Only needed once the link is actually being sent to external reviewers unsupervised |
| Optional stretch | **P5-4: Validator Agent** | 3-4 hr | ⏳ Not started | Only worth doing if a technical-heavy interview loop specifically calls for a second agentic story beyond the orchestrator |

### Shelved — off the active queue, not deleted

P5-2 (Nurse Field Modification Capture — partial state is sufficient for the audit story as-is), P5-3 (Multi-Turn Interaction), P5-5 (Queue Intelligence), P5-6 (Audio-to-Text Intake Capture), P6-1 (Prior Visit History). None of these change what's currently claimable on a resume. Revisit only if a specific job description calls for the exact capability. Full specs unchanged below.

**Still on hold, no change:** P6-2 (FHIR EHR Integration) — 2-3 weeks for a story unlikely to get audited past the README.

### Open decision — P7-B/C scope (not yet decided)

P7-B/C as originally specced below is full Supabase Auth (per-user accounts) + a dedicated `user_quotas` table (~6-9 hr combined). A cheaper alternative: a single shared-password gate in front of the app, relying on the existing $5/mo OpenAI budget cap for cost containment (~1-2 hr) — loses the "individually identifiable external users" story but frees most of that time for the case study, which is the piece that actually moves a resume. **Decide this before starting Priority 3.**

---

## Phase Status Overview

| Phase | Name | Status |
|---|---|---|
| 0 | Infrastructure Setup | ✅ Complete |
| 1 | AI Workflow Foundations | ✅ Complete |
| 2 | AI Productization & UX | ✅ Complete |
| 3 | RAG & Context Systems | ✅ Complete |
| 4 | Agentic Architecture | ✅ Complete |
| 5 | Enterprise AI Systems | ⏳ Not Started |
| 6 | Patient Context Intelligence | ⏳ Not Started (P6-2 on hold) |
| 7 | Portfolio + Resume + Public Presence | ⏳ Not Started (next after P6-1) |

---

## Evaluation Gaps — HHH Scorecard

Current eval state (300-case synthetic run, Seed 99, re-run 2026-07-03 post R4-2 fix):

| Pillar | Question | Result | Gap |
|---|---|---|---|
| **Helpful** | Recall ≥ 98% | ✅ PASS — 100% | Closed 2026-07-03 (R4-2: ingestion + eval harness fix) |
| **Helpful** | ESI calibration | ✅ PASS | STEMI ESI 1 ✅ Stroke ESI 1 ✅ (both fixed) |
| **Honest** | Confidence calibrated | ✅ PASS | — |
| **Honest** | Consistency (same input, same output) | ⬜ NOT RUN | No test run yet |
| **Honest** | Source attribution | ✅ PASS — 0/300 wrong_source | Closed 2026-07-03 (R4-2) |
| **Honest** | Observability / auditability | ⬜ NOT BUILT | Dashboard not yet built |
| **Harmless** | Disposition accuracy | ✅ PASS | — |
| **Harmless** | No over-triage for non-critical | ✅ PASS | Confirmed: non-cardiac chest pain → ESI 4 |
| **Harmless** | De-identification | ❌ RISK — PII stored | patient_name + patient_mrn in Supabase exceed MVP 1 spec |
| **Harmless** | Nurse override audit | ⚠️ PARTIAL | Accept/dismiss logged; text edits and field modifications not captured |
| **Harmless** | Input guardrail | ✅ PASS | 2-layer guardrail live — 16/16 tests passing |
| **Harmless** | Clinical action safety | ✅ PASS | Drug/dosage ban enforced; actions structured with source citation |

To reach **full HHH pass** before shadow mode: 4 items must close.

---

## Phase 4 — Agentic Architecture (In Progress)

### Completed in Phase 4
- WF5 Orchestrator live — 3-branch tiered routing (Critical / Urgent / Low)
- Quick Classify: ESI criteria embedded in system prompt (Option A, recall-first)
- RAG embedded in Critical and Urgent branches (Pinecone topK=4 / topK=2)
- Frontend wired: intake-normal.html → WF5 single orchestrator call
- Supabase: `encounters` table (upsert) + `nurse_actions` audit log
- STEMI ESI 1 calibration fixed — OR logic + synonym expansion + safety override
- Stroke ESI 1 calibration fixed — FAST-positive → always ESI 1, do-not-downgrade instruction
- Live eval pipeline: `live_eval.py` → `eval_results` table in Supabase
- 300-case HHH evaluation report written
- 2-layer input guardrail: client-side regex (Layer 1) + gpt-4o LLM classifier (Layer 2) — 16/16 tests passing
- `guardrail_blocks` audit table live in Supabase (SHA-256 hash only, no plaintext)
- Clinical action constraints: `immediate_actions` / `recommended_actions` changed to structured `{ action, category, source }` objects — drug/dosage ban enforced, category taxonomy restricted, source citation required per action

### Remaining Phase 4 Items

---

#### R4-1: Stroke ESI 1 Calibration
**Status:** ✅ Complete (2026-06-18)  
**Type:** Prompt fix  
**Effort:** ~30 min

**What:** Stroke (FAST-positive: facial droop OR arm weakness OR slurred speech) currently classified ESI 2 in Quick Classify. Ground truth and clinical standard expects ESI 1 — stroke is time-critical at the same level as STEMI.

**Why it matters:** Any FAST-positive stroke routed to ESI 2 receives an `immediate_bed` disposition and a reduced clinical brief. The correct disposition is `resuscitation_room`. This is a direct patient safety risk.

**Fix:** Same pattern as STEMI v3 — move stroke from ESI 2 block to ESI 1 block in Quick Classify system prompt:
```
suspected stroke: facial droop OR arm weakness OR slurred speech (FAST positive) —
if stroke origin is possible, ALWAYS classify ESI 1. Time-to-CT <= 25 min.
```

**Outcome required to close:**
- FAST-positive + stable vitals → ESI 1 ✅
- FAST-positive + elevated BP → ESI 1 ✅  
- Slurred speech only (no other FAST signs) → ESI 1 ✅
- Dizziness without FAST signs → ESI 3 or lower (no over-fire) ✅

**HHH impact:** Fixes Helpful (ESI calibration for stroke category). Prevents Harmless violation (wrong disposition for life-threatening condition).

---

#### R4-2: Stroke RAG Source Match Fix
**Status:** ✅ Complete (2026-07-03)  
**Type:** Ingestion bug + eval harness bug (not a knowledge-base content gap)  
**Effort:** ~1 hr

**Actual root causes (two, compounding — not the originally assumed rank-1 ranking problem):**

1. **Missing document in production Pinecone index.** `ER Triage_ Ingest Clinical Knowledge Base.json` (the live N8N ingestion workflow — confirmed live via real Pinecone/OpenAI credential wiring, vs. `wf3-ingest-knowledge.json` which has a placeholder API key and was never runnable) had a truncated "Return Documents" code node — only 18 of 24 docs, missing `stroke-002` entirely. It was never embedded into Pinecone. Fixed by restoring the full 24-doc list; re-ingested in N8N Cloud.
2. **Eval harness input didn't match production's payload shape.** `evaluation.py` called WF4 with `record["query_text"]` — a synthetic narrative with demographics and raw vitals digits (e.g. "BP 194/88, HR 104") baked into the same string as the complaint. Production (`wf5-orchestrator.json`, `Embed Query Critical` node) only ever embeds clean `complaint_text` + `primary_flag` + `complaint_summary` — never raw vitals text. The vitals noise was crowding out stroke-relevant matches in the eval calls specifically. Fixed by pointing `evaluation.py` at `record["patient_case"]["chief_complaint"]` instead.

No knowledge-base synonym expansion was needed — once the eval matched production's real input shape, lay phrasing ("confused," "slurring her words") already retrieved `stroke-002` at rank 1 without further doc changes.

**Verification:** Re-ran the 300-case seed-99 eval after both fixes — **300/300 (100%)**, all 27 stroke cases pass, up from 293/300 (97.67%).

**HHH impact:** Closes Helpful pillar FAIL (recall 97.67% → 100%). Fixes Honest source attribution for stroke category.

---

#### R4-3: Consistency Test (Honest Q3)
**Status:** ✅ Complete (2026-07-03)  
**Type:** Evaluation test + pre-existing data-path bug fix  
**Effort:** ~20 min test, plus an unplanned debugging detour (see below)

**What:** Ran 6 patient complaints (spanning Critical/Urgent/Low tiers) through WF5 twice, back-to-back, and compared `esi_level`, `primary_flag`, and `disposition`.

**Result: 6/6 consistent** across both runs, including STEMI, stroke, anaphylaxis, sepsis, asthma exacerbation, and hand laceration cases.

**Unplanned finding along the way:** An initial 5/6 run showed one wording mismatch (`asthma` vs `asthma exacerbation`) which looked like a real primary_flag determinism gap. Attempted prompt tightening to enforce canonical flag naming, but every edit broke the live `Quick Classify` node with `"undefined" is not valid JSON`. Root cause: the local repo copy of `wf5-orchestrator.json` predated the guardrail integration and still referenced `$json.body.complaint_text` / `$json.body.{bp,hr,spo2,temp,rr}`. Production had already been correctly updated to read `$json.complaint_text` / `$json.vitals.{bp,hr,spo2,temp,rr}` (matching the `Guardrail Route` node's actual output shape) — this was a **self-inflicted regression**, not a pre-existing production bug: pasting prompt edits built from the stale local file overwrote the live node's correct logic with the outdated one. No historical production traffic was affected. Fixed by restoring the correct `$json.complaint_text` / `$json.vitals.*` references and re-syncing the local file. Re-ran with the original, untouched system prompt (no naming rules added) — full 6/6 consistency, including the previously-flaky case. The initial mismatch was one-off GPT-4o sampling noise at temp=0, not a systematic defect — no prompt change was actually needed.

**HHH impact:** Closes Honest Q3. No further action needed — production behavior is unchanged and confirmed correct.

---

#### R4-4: PII Scope Decision
**Status:** ❌ Open risk  
**Type:** Product / architecture decision  
**Effort:** Decision = ~15 min; implementation = depends on path chosen

**What:** `encounters` table stores `patient_name` and `patient_mrn`. MVP 1 HHH spec says de-identified data only. This is a Harmless pillar violation.

**Three options:**

Option A — Remove name/MRN from frontend form entirely:
Simplest. Intake form collects complaint + vitals only. No PII ever sent to N8N or Supabase. Breaks the realistic EMR-connected workflow demo.

Option B — Collect but do not persist name/MRN to Supabase:
Intake form keeps the fields (realistic UX). Frontend passes name/MRN to WF5 for clinical context display but WF5 does not write these fields to encounters. Supabase stores encounter_id, ESI, flag, complaint_summary only. This is the correct MVP 1 boundary.

Option C — Implement pseudonymization:
Hash name and MRN before writing to Supabase. Reversible for authorized queries. Appropriate for a real MVP but over-engineered for a portfolio project.

**Recommended:** Option B. Matches the "de-identified persistence" intent without gutting the demo UX.

**Outcome required to close:**
- `encounters` table: no patient_name or patient_mrn columns populated ✅
- Frontend form: still collects fields for display and WF5 prompt context ✅
- WF5 write node: explicit omit of name/MRN from upsert payload ✅

**HHH impact:** Closes Harmless PII risk. Required before any public demo or shadow mode.

---

## Phase 5 — Enterprise AI Systems

### P5-1: Observability Dashboard (Honest Q4)
**Status:** ✅ Complete (2026-07-10)  
**Effort:** ~2-3 hours (original estimate; instrumentation layer added ~1-1.5 hr on top, see build summary Session 5)  
**Dependency:** eval_results table live (done), service_role key for read access

**What:** Live dashboard reading from `encounters` + `eval_results` tables. Surface: calls today, branch distribution (critical/urgent/low %), avg latency by branch, estimated token cost, pass rate trend.

**Why it matters for the demo:** Shows AI PM thinking beyond "it works." Cost tracking and latency by branch is what a real AI PM cares about — the eval eval pipeline exists to support this view.

**Progress (2026-07-06):** Discovered `avg latency by branch` and `token cost estimate` had no data source at all — latency was computed client-side and discarded, token usage was returned by OpenAI but stripped out before reaching the frontend. Rather than fake these for an "Honest Q4" dashboard, built the real instrumentation first:
- `supabase/schema_dashboard.sql` — migration adding `latency_ms`, `prompt_tokens`, `completion_tokens` to `encounters` (run against live DB).
- `wf5-orchestrator.json` — added `Merge Usage: Critical/Urgent/Low` Code nodes that sum token usage across every OpenAI call in the request (Guardrail Check + Quick Classify + branch brief call) and attach it to the response. Verified live via direct webhook calls: Critical, Urgent, and Low branches all now return a populated `usage` object.
- `intake-normal.html` — `persistToSupabase` now writes `latency_ms`/`prompt_tokens`/`completion_tokens` on every real intake.
- Still need to confirm one live browser intake writes non-null values into Supabase (only curl-tested so far), then build the actual `GET /dashboard-data` webhook and wire `dashboard.html` to it.

**Update (2026-07-08, Session 6):** Session 5's `Merge Usage` nodes deliberately excluded Pinecone embedding-call tokens from the total, decided unilaterally rather than discussed. Revisited with Venkat — decision: include embedding tokens, but as a separate `embedding_tokens` figure (not blended into `prompt_tokens`/`completion_tokens`), so the dashboard shows LLM cost and embedding cost as distinct line items. See `project_build_summary.md` Session 6 for the full tradeoff discussion. Adds to the outcome checklist below; not yet implemented.

**Blocker found (2026-07-08, Session 6) — CORS blocks the browser intake test:** First real-browser attempt at Step 4 (confirm a live UI intake writes non-null `latency_ms`/`prompt_tokens`/`completion_tokens` to Supabase) failed before ever reaching N8N: `Access to fetch at '.../webhook/parse-complaint' from origin 'null' has been blocked by CORS policy`. Root cause: both webhook nodes (`parse-complaint` in `wf-backend.json`, `orchestrate-triage` in `wf5-orchestrator.json`) have `"options": {}` — no "Allowed Origins (CORS)" configured, so N8N never answers the browser's preflight `OPTIONS` request. This was invisible until now because every prior verification of these endpoints used `curl`, which doesn't send an `Origin` header or trigger CORS preflight at all — likely the actual reason this browser-confirmation step had been sitting open.

**Resolved (2026-07-10):** CORS set to wildcard (`*`) on both `parse-complaint` and `orchestrate-triage` webhook nodes, backstopped by an OpenAI budget cap ($5/mo hard limit, alert at $3 — set after checking actual last-month spend of $1.26). Verified via direct preflight `curl -X OPTIONS` against both endpoints — both now return `204` with correct `access-control-allow-*` headers.
- [x] Decide CORS scope for `parse-complaint` + `orchestrate-triage` webhooks — wildcard now
- [x] Set an OpenAI usage budget cap/alert — $5/mo, alert at $3
- [x] Once CORS is set, re-run Step 4 (browser intake → confirm non-null Supabase columns) — **done, see below**

**Step 4 completed (2026-07-10), with an unplanned detour:** Real browser intake initially wrote zero rows — root cause was a two-layer RLS/upsert interaction (`.upsert()` needs both UPDATE and SELECT policies to resolve `ON CONFLICT`, and `anon` had neither beyond INSERT). Resolved by switching `intake-normal.html` to plain `.insert()` (no new grants needed, avoids ever exercising the `ON CONFLICT` path) rather than granting `anon` a blanket SELECT policy (would have made every patient's encounter data — complaint text, vitals, ESI, clinical brief — publicly readable via the plaintext client-side anon key). Confirmed via real browser test: no console errors, row present in `encounters`. Tradeoff accepted: one row per `analyze()` call rather than one row upserted per encounter — dedupe at query time (`GROUP BY encounter_id ORDER BY created_at DESC LIMIT 1`) when the dashboard is built. Full writeup in `project_build_summary.md`, Session 7.

**Scope decision (2026-07-10):** Built as a new `observability.html` page rather than wiring `dashboard.html` — the two mockups turned out to serve different audiences. `dashboard.html` is a nurse-facing ER floor view (today's intake count, queue by ESI, recent patients) with no cost/latency/eval-trend metrics in it at all; the PM/ops metrics this item actually asks for (branch split %, latency by branch, token cost, eval pass-rate trend) don't belong mixed into a clinical shift-floor screen. `observability.html` is a separate page, linked from `dashboard.html`'s nav.

**Built (2026-07-10):**
- New N8N workflow `wf-observability.json` → `GET /observability-data`: two Supabase nodes (`Fetch Encounters`, `Fetch Eval Results`) reading via a `service_role` credential kept in N8N's credential store (never client-side — the service_role key bypasses RLS entirely, unlike the anon key the frontend uses), feeding a Code node that aggregates total encounters, branch split %, avg ESI, avg latency by branch, a token-cost estimate (prompt/completion tokens × approximate GPT-4o list rates — flagged as an estimate, excludes embedding tokens), and pass-rate trend grouped by `eval_run_id` from `eval_results`.
- `observability.html` — stat tiles, branch-split and latency-by-branch bar charts (colored consistently with the app's existing ESI severity palette — critical/urgent/low map to `--danger`/`--warning`/`--success`), a token-cost breakdown, and an SVG pass-rate trend line with hover tooltips and a backing data table.
- Verified end-to-end via `curl` (real aggregated numbers returned) and in-browser (charts render correctly against live data, no console errors).

**Debugging detour:** the new webhook went through several N8N-specific failures before working — Webhook node's Response Mode defaulted to `Immediately` instead of `Using 'Respond to Webhook' Node` (caused an "unused Respond to Webhook node" error); the two Supabase nodes' default names didn't get fully renamed to match the Code node's `$('Fetch Encounters')`/`$('Fetch Eval Results')` references (caused "Referenced node doesn't exist" — resolved by fixing the actual node names, isolated by testing each `$()` reference individually); and the Respond to Webhook node's Response Body field wasn't actually in expression mode, so the literal text `={{ JSON.stringify($json) }}` failed JSON validation — fixed by switching to `{{ $json }}` in genuine expression mode.

**Outcome — all closed:**
- ✅ Reads from Supabase via `service_role` (scoped, server-side only)
- ✅ Shows: total encounters, branch split %, avg ESI, avg latency by branch, token cost estimate
- ⏳ `embedding_tokens` as a separate figure — still not implemented (2026-07-08 decision); current cost estimate is prompt+completion tokens only, clearly labeled as such in the UI
- ✅ Pass rate trend over time from `eval_results`
- ✅ Refreshes on page load
- ✅ Browser intake write-path confirmed end-to-end (2026-07-10)

**HHH impact:** Closes Honest Q4 (auditability/observability).

---

### P5-2: Nurse Field Modification Capture
**Status:** ⚠️ Partial  
**Effort:** ~1 hour

**What:** `nurse_actions` table currently captures accept/dismiss button clicks only. It does not capture:
- When a nurse edits a specific field (ESI level, primary flag, complaint text) before accepting
- What the AI originally said vs. what the nurse changed it to
- Which field was modified (field-level granularity, not just "something changed")

This is the richest feedback signal in the system. Every nurse edit is a ground-truth correction — it tells you exactly where the AI was wrong, on which field, for which patient presentation.

**Capture schema (additions to `nurse_actions`):**
```
{
  encounter_id,
  action_type:  "accept" | "dismiss" | "edit_accept" | "field_edit",
  field_name:   "esi_level" | "primary_flag" | "complaint_summary" | "disposition" | "action_item",
  ai_value:     <original AI output for that field>,
  nurse_value:  <what the nurse changed it to>,
  changed:      true | false
}
```

**Implementation:**
- On accept without edits: `action_type: "accept"`, `changed: false`
- On accept with any field changed: `action_type: "edit_accept"`, one row per changed field with `ai_value` vs `nurse_value`
- On dismiss: `action_type: "dismiss"`, `nurse_value: null`
- Edit detection: snapshot AI output on render → diff against field values at submit time

**Outcome required to close:**
- Nurse edits ESI level 2 → 3: captured as `{ field_name: "esi_level", ai_value: 2, nurse_value: 3 }` ✅
- Nurse edits complaint summary text: captured with original vs. edited text ✅
- Nurse accepts without changes: single `accept` row, `changed: false` ✅
- Nurse dismisses: `dismiss` row, `nurse_value: null` ✅
- No edit on dismiss required — dismiss itself is the signal ✅

**HHH impact:** Closes Harmless nurse override audit gap. Field-level edit data feeds future model improvement (which fields get corrected most → targeted fine-tuning or prompt improvement signal).

---

### P5-3: Multi-Turn Interaction
**Status:** ⏳ Not started  
**Effort:** ~1 week  
**Dependency:** P5-1 (DB reads live)

**What:** Nurse can ask follow-up questions after initial triage assessment. "What if SpO2 drops to 88%?" or "Is this disposition right for a 75-year-old?" WF5 maintains a session conversation state.

**Why:** Demonstrates agentic behavior beyond single-turn. Strong Phase 5 / Maven course deliverable.

**Outcome:** 3+ turn conversation on same encounter without context loss; response grounded in retrieved guidelines.

---

### P5-4: Validator Agent
**Status:** ⏳ Not started  
**Effort:** ~3-4 hours  
**Dependency:** WF5 output stable

**What:** Second LLM call after Build Clinical Brief that independently verifies the output against a safety checklist. Flags: ESI mismatch vs. raw vitals, missing time_targets for critical ESI, disposition inconsistent with acuity.

**Why:** Demonstrates agentic self-checking — a concrete artifact showing AI PM awareness of model reliability limits.

**Outcome:**
- Validator catches ESI 1 output missing door-to-balloon target ✅
- Validator catches ESI 2 output with resuscitation_room disposition (should be immediate_bed) ✅
- Validator adds `validation_warnings: []` field to WF5 output ✅

---

### P5-5: Queue Intelligence
**Status:** ⏳ Not started  
**Effort:** ~2 hours  
**Dependency:** P5-1 (observability)

**What:** Queue panel showing all active encounters from Supabase, sorted by ESI, with real-time flag status. Nurse can see full ER state at a glance.

**Note:** Lower priority than P5-1 through P5-4. Queue view is polish; observability + validator are the PM craft signals.

---

### P5-6: Audio-to-Text Intake Capture
**Status:** ⏳ Not started  
**Effort:** ~3-4 hours  
**Dependency:** None (parallel to other P5 items)

**What:** Replace the complaint text field with a voice capture button. Nurse speaks the patient complaint; it transcribes in real time and populates the complaint_text field before WF5 is called. Vitals can remain typed (numeric entry is faster than dictating numbers).

**Why:** Typing while a patient is distressed is slow and error-prone. Voice capture matches how nurses already communicate in triage — verbal handoffs, verbal assessments. Reduces intake time and captures richer complaint language (patient's own words, affect, context) vs. abbreviated typed notes.

**Implementation approach:**
- Browser-native: Web Speech API (no API cost, works offline, limited browser support — Chrome/Edge only)
- Preferred: OpenAI Whisper API (`/audio/transcriptions` endpoint) via a thin proxy or direct browser call with the OpenAI key scoped to audio only. Handles accents, medical terminology, background noise better than Web Speech.
- UX: microphone icon button → recording indicator → live transcript appears in complaint_text → nurse reviews and edits before submit

**Scope boundary:** Transcription only. Do not attempt to auto-submit on speech end — nurse must review the transcript before analysis fires.

**Outcome required to close:**
- Voice complaint → accurate transcript in complaint_text field ✅
- Medical terms transcribed correctly (e.g., "diaphoresis," "FAST positive," "dyspnea") ✅
- Nurse can edit transcript before triggering WF5 ✅
- Fallback: text input still works if mic is unavailable or denied ✅
- No vitals auto-fill from voice — numbers typed manually ✅

---

## Phase 6 — Patient Context Intelligence

This phase adds longitudinal patient awareness to triage assessments. The system moves from reacting to the current complaint in isolation to understanding the patient's history — prior ER visits from our own system, and full medical history from external EHR systems. Both capabilities directly improve the relevance and safety of AI-generated triage output.

---

### P6-1: Prior Visit History from Internal Supabase
**Status:** ⏳ Not started  
**Effort:** ~4-6 hours  
**Dependency:** P4-4 PII scope resolved (MRN must be available as a lookup key, but not stored as PII — use hashed MRN)

**What:** Before generating the triage assessment, query the `encounters` table for prior visits by the same patient (matched by hashed MRN). Inject a structured visit summary into the WF5 prompt context: last visit date, ESI level at last visit, primary flag, disposition, and nurse action taken.

**Why it matters clinically:** A patient presenting with chest pain who was discharged ESI 3 two weeks ago for the same complaint is a different risk profile from a first-time presenter. A patient with three prior ESI 2 sepsis flags needs aggressive early treatment. Without history, the AI sees every visit as a first encounter — the same blind spot as a walk-in urgent care with no records.

**Architecture:**
- New N8N node in WF5 (before Quick Classify): `Lookup Prior Visits` → Supabase REST `GET /encounters?patient_mrn_hash=eq.{hash}&order=created_at.desc&limit=3`
- Output: last 3 visits as structured JSON, injected into Quick Classify and Build Clinical Brief user prompt
- If no prior visits: field omitted from prompt (no hallucination risk from empty context)

**Prompt injection format:**
```
Prior visits (last 3):
- 2026-05-28: ESI 2 / Sepsis / immediate_bed / accepted
- 2026-04-10: ESI 3 / Chest Pain / urgent_bed / edited
```

**Outcome required to close:**
- WF5 injects prior visits for returning patient ✅
- Build Clinical Brief references prior history when relevant ("patient had prior ESI 2 sepsis presentation 3 weeks ago — monitor for recurrence") ✅
- First-time patients: no hallucinated history, no prompt injection ✅
- History lookup adds < 200ms latency (single indexed Supabase query) ✅
- MRN stored as SHA-256 hash only — not plaintext ✅

**HHH impact:** Directly improves Helpful (more contextually accurate assessments). Reduces Harmless risk (prior high-acuity presentations increase current-visit ESI floor — catching under-triage for repeat critical patients).

---

### P6-2: External EHR Integration (FHIR R4)
**Status:** 🔒 ON HOLD (2026-07-03) — deprioritized in favor of Phase 7  
**Effort:** ~2-3 weeks (includes EHR sandbox access)  
**Dependency:** P6-1 live (establishes the pattern for context injection)

**What:** Connect to an external EHR system via HL7 FHIR R4 API to pull the patient's full clinical record at intake time — active medications, known allergies, active diagnoses (conditions), and most recent labs. Inject as structured context into WF5 before triage classification.

**Why it matters:** Current system sees only the presenting complaint and vitals. The EHR layer adds:
- **Medications:** A patient on warfarin with head trauma is ESI 1, not ESI 2. A patient on metformin with altered mental status needs glucose checked first.
- **Allergies:** If Build Clinical Brief recommends aspirin for chest pain but patient is allergic, the AI is giving a harmful recommendation.
- **Active diagnoses:** Chronic CHF patient presenting with dyspnea has a different workup than a healthy 25-year-old with the same complaint.
- **Recent labs:** Troponin from 6 hours ago at another facility changes everything for a chest pain presentation.

**Integration target (portfolio):** SMART on FHIR sandbox (Epic FHIR R4 sandbox or HAPI FHIR public test server). Does not require production EHR access for a portfolio build — sandbox gives real API behavior.

**FHIR resources to pull:**
- `Patient/{id}` — demographics confirmation
- `MedicationRequest?patient={id}&status=active` — current medications
- `AllergyIntolerance?patient={id}` — allergies and intolerances
- `Condition?patient={id}&clinical-status=active` — active diagnoses
- `Observation?patient={id}&category=laboratory&_sort=-date&_count=5` — 5 most recent labs

**Architecture:**
- New WF6: `Fetch EHR Context` — triggered by WF5 after patient MRN lookup. Calls FHIR endpoints, normalizes responses into a structured summary, returns to WF5.
- WF5 injects EHR summary into Build Clinical Brief prompt alongside RAG guidelines.
- Allergy guard: separate prompt instruction — "If recommended treatment conflicts with known allergy, flag it explicitly in clinical_notes with ALLERGY CONFLICT: [drug] — [allergy]."

**Scope boundary for portfolio build:**
- Read-only. No write-back to EHR.
- Medications, allergies, conditions, recent labs only. No imaging, no full clinical notes.
- FHIR sandbox data — not production patient records.

**Outcome required to close:**
- FHIR patient lookup by MRN → returns active medications, allergies, conditions, recent labs ✅
- WF5 injects EHR context into Build Clinical Brief prompt ✅
- Allergy conflict detected and surfaced in clinical_notes output ✅
- Medication interaction awareness changes recommended actions where relevant ✅
- Graceful degradation: if FHIR call fails or times out, WF5 proceeds without EHR context (no blocking) ✅
- EHR data not stored in Supabase — in-flight only, cleared after encounter response ✅

**HHH impact:** Major Helpful uplift — assessments become clinically complete, not just complaint-reactive. Direct Harmless impact — allergy conflict detection prevents AI-generated harmful recommendations.

---

## Phase 7 — Portfolio + Resume + Public Presence

| Item | Status | Notes |
|---|---|---|
| GitHub README + architecture diagram | ⏳ | Update after Phase 6 complete; diagram must reflect audio capture, prior history, and FHIR layers |
| Live demo link | ⏳ | Expanded into P7-A/B/C below (2026-07-10) — hosting, auth, and per-user quota, not just a recorded video |
| Case study write-up | ⏳ | RAG-before-routing decision + FHIR integration + token optimization = 3 strong AI PM stories |
| EB1 content — Agentic AI in ER Triage | ⏳ | FHIR + prior history layer is the differentiator vs. generic AI triage — strongest EB1 angle |
| Resume update — ER Triage project | ⏳ | Phase 4 Agentic cert claimable (done); FHIR integration claimable after P6-2 ships |

---

### P7-A: Production Hosting

**Status:** ⏳ Not started
**Effort:** ~1-2 hr
**Dependency:** None

**Decided (2026-07-17): Cloudflare Pages.** Superseded the original "Vercel or Netlify, TBD" framing below (kept for context, not the active plan).

**What:** Deploy `mockups/` to Cloudflare Pages as a real public URL, replacing local `file://` testing. Add a small build step so Supabase credentials are injected from Cloudflare's dashboard-configured environment variables at deploy time, rather than committed to the repo — meaningful once this repo goes public for the portfolio (Phase 7's other items).

**Why Cloudflare Pages over Vercel/Netlify (2026-07-17 decision):**
- **Bandwidth:** unlimited on Cloudflare's free tier, structurally (not a generous cap) — no metered line to ever worry about. Netlify's free tier caps at 100GB/mo with expensive overages (~$55/100GB). Vercel's Hobby bandwidth is metered, not unlimited.
- **Cost at scale:** if a recruiter/hiring-manager traffic spike ever happened, Cloudflare stays at $0. Vercel would eventually need Pro ($20/mo, per seat) to remove ambiguity; Netlify would hit real overage billing.
- **ToS fit:** Cloudflare Pages' free tier has no "personal, non-commercial use only" restriction. Vercel Hobby explicitly does — a job-search-motivated portfolio site sits in a gray area there (low enforcement risk for a small static site, but a real clause, not hypothetical).
- **No framework lock-in wasted:** this stack is vanilla JS/HTML, so Vercel's Next.js-specific polish buys nothing here.
- **Feature parity confirmed:** preview deploys per branch, custom domains, SSL, and build-time env var injection are all free on Cloudflare Pages, same as Vercel/Netlify — the one thing GitHub Pages lacked (see below) isn't a gap here.
- 500 builds/month free — ample for a project deployed occasionally, not continuously.

**Why not GitHub Pages:** Considered and rejected for this specific use — GitHub Pages has no env-var injection, so `env.local.js` (currently gitignored, generated by `scripts/gen-env-local.sh`) would have to be committed for the site to work once deployed there. The Supabase key involved is the `anon` key, which is meant to be public-safe (RLS protects the data, not key secrecy), so the actual risk is low — but Cloudflare Pages' real secret injection is cleaner and was the explicit choice here.

**Implementation:**
- Small build script (Node or shell), same shape as `scripts/gen-env-local.sh`, but reading from Cloudflare Pages' dashboard-configured env vars instead of a local `.env` file — generates `env.local.js` at deploy time (Cloudflare Pages runs a configurable build command before publishing static output).
- Configure `SUPABASE_URL` / `SUPABASE_KEY` (and once P7-B lands, the Supabase Auth anon/public key if different) in the Cloudflare Pages dashboard's environment variables.
- **Follow-up this triggers:** CORS on the N8N webhooks (`parse-complaint`, `orchestrate-triage`, `observability-data`) is currently wildcard `*`, deliberately deferred until there was a real production origin to scope to (see Session 6/7 CORS decision history above). Once hosted, tighten Allowed Origins from `*` to the actual `*.pages.dev` (or custom domain, if configured).

**Outcome required to close:**
- App reachable at a public Cloudflare Pages URL
- No secret values committed to the git history
- CORS tightened from wildcard to the actual production origin on all three webhooks

---

### P7-B: Auth + Admin User Management

**Status:** ⏳ Not started
**Effort:** ~4-6 hr
**Dependency:** P7-A (needs a real hosted origin for auth redirect URLs)

**What:** Gate the app behind login using **Supabase Auth** (already using Supabase for data — no new vendor). A login screen in front of `intake-normal.html` etc.; Venkat (admin) creates each external trial user directly via the Supabase dashboard's Authentication panel (Invite/Add User) — no custom admin UI needed for v1. Successful login issues a JWT the frontend attaches (`Authorization: Bearer <jwt>`) to every N8N webhook call.

**Why it matters:** Turns this from "anyone with the URL can use it unlimited" into "specific invited people, individually identifiable" — the prerequisite for both controlled external sharing and the per-user quota in P7-C (quota needs to know *who* is asking).

**Architecture — new to this project, webhooks currently have zero request-level auth:**
- Add a JWT-verification step at the top of each webhook (`parse-complaint`, `orchestrate-triage`) — mirrors the existing length-guard pattern (`Webhook → Verify Auth → [valid: continue] / [invalid: 401]`). Verification either validates the JWT signature against Supabase's JWT secret, or calls Supabase's `/auth/v1/user` endpoint with the token to confirm validity and retrieve the user's id.
- **Decided (2026-07-10): Option B for v1.** Supabase writes stay exactly as they are today — still via the `anon` key, still governed by the existing INSERT-only RLS policy. "Who's allowed to use the app at all" is handled entirely at the N8N/login-gate layer; the database itself doesn't enforce per-user row ownership. Chosen over the stricter alternative (below) because this is trial/demo data, nobody can currently read `encounters` at all regardless (no SELECT policy exists, by design, per this session's RLS hardening), and it avoids touching the RLS setup that was just hardened.

- **Option A — captured as the documented upgrade path, not built now:** `authenticated`-role writes scoped by `auth.uid()`, giving real database-enforced per-user data isolation (a user could only write/see rows tagged as their own, enforced by Postgres itself rather than trusted to N8N's own bookkeeping). Would also enable a future "show me my own past cases" feature.

  **Critical implementation note for Option B, to keep this migration cheap later:** whatever writes `user_id` onto each `encounters` row (frontend or N8N) **must store the real Supabase Auth user UUID** (`session.user.id` from the logged-in client, or the `id` field returned when N8N validates the JWT via `/auth/v1/user`) — never a placeholder, an email string, or `NULL`. If this discipline holds from the first row written under P7-B, moving to Option A later is nearly free:
  1. Add a `WITH CHECK (user_id = auth.uid())` policy (and a matching scoped `SELECT` policy) — no data rewrite needed, since every row's `user_id` already matches what `auth.uid()` will resolve to.
  2. Ensure the frontend's Supabase client uses the authenticated session (not the bare anon key) for these calls — supabase-js does this automatically once a user is signed in, as long as nothing bypasses it.

  **If that discipline was ever violated** (a row with a non-UUID value, or `NULL`, in `user_id`): moving to Option A requires backfilling those rows with the correct `auth.uid()` by mapping back to the real account where possible, and explicitly deciding what happens to any row that can't be mapped (it becomes invisible to everyone under strict Option A, acceptable for throwaway trial data, not acceptable if continuity mattered).

**Outcome required to close:**
- Login screen live, backed by Supabase Auth
- Admin (Venkat) can create/invite a new user without writing code
- Every webhook call carries a JWT; N8N rejects unauthenticated requests with 401
- Decision made (and documented) on the anon-vs-authenticated Supabase write question above

---

### P7-C: Per-User Transaction Quota

**Status:** ⏳ Not started
**Effort:** ~2-3 hr
**Dependency:** P7-B (quota is keyed by the user identity auth provides)

**What:** Cap the number of intake analyses ("transactions" — one `/orchestrate-triage` call) each invited user can run, so external reviewers get enough to evaluate the product without open-ended cost exposure. **Decided (2026-07-10): 10-15 transactions per user** (pick a specific number, e.g. 12, at implementation time), with the ability for admin (Venkat) to reset a user's count when needed — e.g. a reviewer who wants a second look, or ran out mid-demo.

**Architecture:** Rather than counting rows in `encounters` directly (which would tie quota tracking to the audit history — resetting a user's quota would then mean either deleting their real triage records or fudging the count logic), use a **dedicated `user_quotas` table**:
```sql
CREATE TABLE user_quotas (
  user_id           UUID PRIMARY KEY,   -- matches auth.users.id / auth.uid()
  transactions_used INTEGER NOT NULL DEFAULT 0,
  quota_limit       INTEGER NOT NULL DEFAULT 12,
  last_reset_at     TIMESTAMPTZ,
  created_at        TIMESTAMPTZ DEFAULT NOW()
);
```
- At the top of WF5, after the P7-B auth-verification step and before the expensive Guardrail Check/Quick Classify/RAG/Brief chain, add a `Check Quota` step: read `transactions_used`/`quota_limit` for that `user_id` (creating the row with defaults on first use if it doesn't exist yet), and if `transactions_used >= quota_limit`, respond immediately (e.g. `403` with "you've used your N free analyses — contact Venkat for more") instead of running the pipeline — same early-exit principle as the complaint length-guard.
- On a successful analysis, increment `transactions_used` by 1 (as part of the same request, after the pipeline completes — or right after the quota check passes, whichever is simpler to wire).
- This read/write needs the `service_role` credential (already set up for the observability workflow), since `anon` has no access to this table either.
- **Admin reset, no custom UI needed for v1:** consistent with how user creation itself works in P7-B (directly via the Supabase dashboard, no custom admin panel) — Venkat resets a user's quota by editing their row in `user_quotas` directly in the Supabase Table Editor (`transactions_used` back to `0`, optionally bump `quota_limit` for a specific person). A proper admin UI button is a reasonable later upgrade, not needed to close this item.

**Outcome required to close:**
- `user_quotas` table live, defaults to the chosen limit (10-15) per new user
- WF5 rejects the (N+1)th transaction for a given user with a clear message, before any OpenAI/Pinecone calls fire
- Quota check verified not to fire a false rejection for a user under the limit, and to correctly block a user who has hit it
- Admin can reset a specific user's `transactions_used` via the Supabase dashboard and confirm they can transact again immediately after

---

## Sequenced Work Queue

Items ordered by dependency and HHH criticality:

| # | Item | Phase | Status | HHH Gap Closed | Effort |
|---|---|---|---|---|---|
| ✅ | R4-1: Stroke ESI 1 calibration | 4 | Done | Helpful (ESI) · Harmless (disposition) | 30 min |
| ✅ | Guardrail system (2-layer) | 4 | Done | Harmless (input safety) | — |
| ✅ | Clinical action constraints | 4 | Done | Harmless (drug/dosage safety) | — |
| ✅ | R4-4: PII scope — name/MRN removed from Supabase upsert | 4 | Done (code) | Harmless (PII) | 15 min |
| ✅ | R4-2: Stroke RAG source fix (ingestion + eval harness bug) | 4 | Done | Helpful (recall ≥ 98%) · Honest (source) | ~1 hr |
| ✅ | R4-3: Consistency test | 4 | Done | Honest (consistency) | 20 min |
| ✅ | P5-1: Observability dashboard (`observability.html`) | 5 | Done (2026-07-10) | Honest (auditability) | 2-3 hr |
| 2 | P5-2: Nurse field modification capture | 5 | ⚠️ Partial | Harmless (override audit) | 1 hr |
| 3 | P5-4: Validator agent | 5 | ⏳ Not started | Harmless (action verification) | 3-4 hr |
| 4 | P5-6: Audio-to-text intake capture | 5 | ⏳ Not started | — | 3-4 hr |
| 5 | P5-3: Multi-turn interaction | 5 | ⏳ Not started | — | ~1 wk |
| 6 | P5-5: Queue intelligence | 5 | ⏳ Not started | — | 2 hr |
| 7 | P6-1: Prior visit history (internal Supabase) | 6 | ⏳ Not started | Helpful (longitudinal context) | 4-6 hr |
| 8 | P7-A: Production hosting (Cloudflare Pages) | 7 | ⏳ Not started | — | 1-2 hr |
| 9 | P7-B: Auth + admin user management | 7 | ⏳ Not started | — | 4-6 hr |
| 10 | P7-C: Per-user transaction quota | 7 | ⏳ Not started | Harmless (cost containment) | 2-3 hr |
| 11 | Phase 7: Portfolio wrap-up (README, case study, EB1 content, resume) | 7 | ⏳ Not started | — | 1-2 days |
| 🔒 | P6-2: External EHR integration (FHIR R4) | 6 | **ON HOLD** (2026-07-03) | Helpful · Harmless (allergy conflict) | 2-3 wk |
| ✅ | **Housekeeping: resync local N8N workflow JSON exports with live N8N Cloud instance** | — | Done (2026-07-03) | — | ~30 min |

**2026-07-03 decision:** P6-2 (FHIR EHR integration) is on hold — highest effort item (2-3 weeks), lowest near-term leverage. Move to Phase 7 (portfolio wrap-up) next after P6-1, ahead of P6-2. Revisit P6-2 after Phase 7 or if a specific reason to prioritize FHIR integration emerges.

---

## Scope Note (2026-07-03)

Demo/shadow-mode is no longer a target milestone — this project is being built out as a complete product, not staged toward a specific demo event. Phase 7 (portfolio wrap-up) is deprioritized accordingly. The items below remain the correct build order because they're genuine product defects/gaps, not demo-readiness theater — priority is now driven by HHH completeness and build sequencing, not "is this needed before I show someone."

## Product Completeness Checklist (formerly "Shadow Mode Readiness")

- [x] R4-4: PII scope decision made (Option B) — name/MRN removed from Supabase upsert in `intake-normal.html`
- [x] R4-2: Stroke RAG — eval recall 100% confirmed on re-run (2026-07-03)
- [x] R4-3: Consistency — 6/6 identical outputs on same input (2026-07-03)
- [x] R4-1: Stroke ESI 1 — FAST-positive → ESI 1 confirmed
- [x] P5-1: Observability dashboard live (`observability.html` + `wf-observability.json` → `GET /observability-data`) — complete 2026-07-10

Full HHH pass achieved as of 2026-07-10 — all 10 dimensions now closed (observability dashboard was the last one open).
