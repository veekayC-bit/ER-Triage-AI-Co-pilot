# ER Triage AI Co-pilot — Roadmap
**Project:** ER Assisted Triage Workflow System  
**Stack:** N8N Cloud · OpenAI GPT-4o · Pinecone · Supabase · Vanilla JS  
**Last Updated:** June 18, 2026

---

## Phase Status Overview

| Phase | Name | Status |
|---|---|---|
| 0 | Infrastructure Setup | ✅ Complete |
| 1 | AI Workflow Foundations | ✅ Complete |
| 2 | AI Productization & UX | ✅ Complete |
| 3 | RAG & Context Systems | ✅ Complete |
| 4 | Agentic Architecture | 🔄 In Progress |
| 5 | Enterprise AI Systems | ⏳ Not Started |
| 6 | Portfolio + Resume + Public Presence | ⏳ Not Started |

---

## Evaluation Gaps — HHH Scorecard

Current eval state (300-case synthetic run, Seed 99):

| Pillar | Question | Result | Gap |
|---|---|---|---|
| **Helpful** | Recall ≥ 98% | ❌ FAIL — 97.67% | 7 Stroke Indicator wrong_source failures |
| **Helpful** | ESI calibration | ✅ PASS (post-STEMI fix) | STEMI: done. Stroke ESI 1 fix still pending. |
| **Honest** | Confidence calibrated | ✅ PASS | — |
| **Honest** | Consistency (same input, same output) | ⬜ NOT RUN | No test run yet |
| **Honest** | Source attribution | ❌ FAIL — 7/300 wrong_source | Stroke cases: ESI-2 doc outranks stroke-specific docs |
| **Honest** | Observability / auditability | ⬜ NOT BUILT | Dashboard not yet built |
| **Harmless** | Disposition accuracy | ✅ PASS | — |
| **Harmless** | No over-triage for non-critical | ✅ PASS | Confirmed: non-cardiac chest pain → ESI 4 |
| **Harmless** | De-identification | ❌ RISK — PII stored | patient_name + patient_mrn in Supabase exceed MVP 1 spec |
| **Harmless** | Nurse override audit | ⚠️ PARTIAL | Accept/dismiss logged; text edits not captured |

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
- Live eval pipeline: `live_eval.py` → `eval_results` table in Supabase
- 300-case HHH evaluation report written

### Remaining Phase 4 Items

---

#### R4-1: Stroke ESI 1 Calibration
**Status:** ⏳ Not started  
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
**Status:** ⏳ Not started  
**Type:** Knowledge base fix  
**Effort:** ~45 min

**What:** 7/300 eval failures all share the same root cause — Pinecone returns the ESI Level 2 guideline at rank #1 for stroke queries because "FAST-positive stroke" is mentioned there too. Stroke-specific documents (`stroke-001`, `stroke-002`) appear in top-4 but not at rank #1. `source_match` is a strict rank-1 check, so all 7 fail.

**Two fix paths (pick one):**

Option 1 — Expand stroke knowledge docs:
Rewrite `stroke-001` and `stroke-002` with denser stroke-specific content (tPA criteria, NIH Stroke Scale, CT protocol timelines). This increases semantic distance between stroke docs and the ESI-2 doc and raises stroke docs to rank #1 for FAST queries.

Option 2 — Relax evaluation metric:
Change `source_match` in `live_eval.py` from rank-1 source check to top-3 source presence. The retrieved content is clinically correct — this is a metrics artifact, not a retrieval failure.

**Recommended:** Option 1. It actually improves retrieval quality and not just the metric.

**Outcome required to close:**
- FAST-positive stroke query → top-1 result from `critical_conditions` source ✅
- Eval recall ≥ 98.0% on re-run ✅ (closes Helpful FAIL)

**HHH impact:** Closes Helpful pillar FAIL (recall 97.67% → ≥ 98%). Fixes Honest source attribution for stroke category.

---

#### R4-3: Consistency Test (Honest Q3)
**Status:** ⬜ Not run  
**Type:** Evaluation test  
**Effort:** ~20 min

**What:** Run the same 5-10 patient complaints through WF5 twice, back-to-back, and compare outputs. Test pass if ESI level, primary_flag, and disposition are identical in both runs.

**Why it matters:** GPT-4o with `temperature: 0` should be deterministic. If outputs vary between identical inputs, there is a stability problem — either in prompt construction, N8N data passing, or model sampling.

**Outcome required to close:**
- All test cases: ESI level identical across both runs ✅
- All test cases: primary_flag identical ✅
- All test cases: disposition identical ✅
- Acceptable variance: clinical_notes wording may differ slightly (string, not scored)

**HHH impact:** Closes Honest Q3. Required before shadow mode claim of "consistent outputs."

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
**Status:** ⏳ Not started  
**Effort:** ~2-3 hours  
**Dependency:** eval_results table live (done), service_role key for read access

**What:** Live dashboard reading from `encounters` + `eval_results` tables. Surface: calls today, branch distribution (critical/urgent/low %), avg latency by branch, estimated token cost, pass rate trend.

**Why it matters for the demo:** Shows AI PM thinking beyond "it works." Cost tracking and latency by branch is what a real AI PM cares about — the eval eval pipeline exists to support this view.

**Outcome required to close:**
- `dashboard.html` reads from Supabase (service_role key scoped read-only) ✅
- Shows: total encounters, branch split %, avg ESI, avg latency, token cost estimate ✅
- Pass rate trend over time from eval_results ✅
- Refreshes on load (no WebSocket required for MVP) ✅

**HHH impact:** Closes Honest Q4 (auditability/observability).

---

### P5-2: Nurse Override Audit Completion
**Status:** ⚠️ Partial  
**Effort:** ~1 hour

**What:** `nurse_actions` table currently captures accept/dismiss button clicks. When a nurse edits the AI suggestion text before accepting, the edit is not captured — only the final click.

**Outcome required to close:**
- On dismiss: capture `{encounter_id, action: "dismiss", ai_value, nurse_value: null}` ✅ (done)
- On edit + accept: capture `{encounter_id, action: "edit_accept", ai_value: <original>, nurse_value: <edited>}` ✅ (not done)
- Edit detection: compare textarea value at submit time against original AI output ✅

**HHH impact:** Closes Harmless nurse override audit gap. Also feeds future override analysis (which conditions get edited most often → model improvement signal).

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

## Phase 6 — Portfolio + Resume + Public Presence

| Item | Status | Notes |
|---|---|---|
| GitHub README + architecture diagram | ⏳ | Update after Phase 5 complete |
| Live demo link | ⏳ | Requires hosting or recorded demo video |
| Case study write-up | ⏳ | RAG-before-routing decision + token optimization = strong AI PM story |
| EB1 content — Agentic AI in ER Triage | ⏳ | Thought leadership article post-demo |
| Resume update — ER Triage project | ⏳ | Phase 4 Agentic cert claimable after May 30, 2026 (done) |

---

## Sequenced Work Queue

Items ordered by dependency and HHH criticality:

| # | Item | Phase | Blocks | HHH Gap Closed | Effort |
|---|---|---|---|---|---|
| 1 | R4-1: Stroke ESI 1 calibration | 4 | Nothing | Helpful (ESI) · Harmless (disposition) | 30 min |
| 2 | R4-4: PII scope — remove name/MRN from upsert | 4 | Shadow mode | Harmless (PII) | 15 min |
| 3 | R4-2: Stroke RAG source fix (expand stroke docs) | 4 | Live eval re-run | Helpful (recall ≥ 98%) · Honest (source) | 45 min |
| 4 | R4-3: Consistency test | 4 | Honest Q3 close | Honest (consistency) | 20 min |
| 5 | P5-1: Observability dashboard | 5 | Honest Q4 close | Honest (auditability) | 2-3 hr |
| 6 | P5-2: Nurse override audit | 5 | Harmless audit close | Harmless (override log) | 1 hr |
| 7 | P5-4: Validator agent | 5 | Agentic demo artifact | — | 3-4 hr |
| 8 | P5-3: Multi-turn interaction | 5 | Maven course deliverable | — | ~1 wk |
| 9 | P5-5: Queue intelligence | 5 | Polish | — | 2 hr |
| 10 | Phase 6: Portfolio wrap-up | 6 | Public demo ready | — | 1-2 days |

---

## Shadow Mode Readiness Checklist

Before moving from internal testing to shadow mode (showing to external stakeholders or embedding in a real ER workflow demo):

- [ ] R4-1: Stroke ESI 1 — FAST-positive → ESI 1 confirmed
- [ ] R4-4: PII — name/MRN not persisted to Supabase
- [ ] R4-2: Stroke RAG — eval recall ≥ 98.0% confirmed on re-run
- [ ] R4-3: Consistency — identical outputs on same input, 5/5 tests
- [ ] R4-4 variant: Disposition valid for all critical flags (STEMI ESI 1 → resuscitation_room, Stroke ESI 1 → resuscitation_room)
- [ ] P5-1: Observability dashboard live (at minimum: encounter count + branch distribution)

Full HHH pass is the gate. 4 of 10 dimensions are open right now.
