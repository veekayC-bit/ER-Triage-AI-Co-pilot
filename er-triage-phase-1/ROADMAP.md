# ER Triage AI Co-pilot — Roadmap
**Project:** ER Assisted Triage Workflow System  
**Stack:** N8N Cloud · OpenAI GPT-4o · Pinecone · Supabase · Vanilla JS  
**Last Updated:** June 18, 2026 (Session 3)

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
| 6 | Patient Context Intelligence | ⏳ Not Started |
| 7 | Portfolio + Resume + Public Presence | ⏳ Not Started |

---

## Evaluation Gaps — HHH Scorecard

Current eval state (300-case synthetic run, Seed 99):

| Pillar | Question | Result | Gap |
|---|---|---|---|
| **Helpful** | Recall ≥ 98% | ❌ FAIL — 97.67% | 7 Stroke Indicator wrong_source failures (RAG source fix pending) |
| **Helpful** | ESI calibration | ✅ PASS | STEMI ESI 1 ✅ Stroke ESI 1 ✅ (both fixed) |
| **Honest** | Confidence calibrated | ✅ PASS | — |
| **Honest** | Consistency (same input, same output) | ⬜ NOT RUN | No test run yet |
| **Honest** | Source attribution | ❌ FAIL — 7/300 wrong_source | Stroke cases: ESI-2 doc outranks stroke-specific docs |
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
**Status:** ⏳ Not started  
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
| Live demo link | ⏳ | Requires hosting or recorded demo video |
| Case study write-up | ⏳ | RAG-before-routing decision + FHIR integration + token optimization = 3 strong AI PM stories |
| EB1 content — Agentic AI in ER Triage | ⏳ | FHIR + prior history layer is the differentiator vs. generic AI triage — strongest EB1 angle |
| Resume update — ER Triage project | ⏳ | Phase 4 Agentic cert claimable (done); FHIR integration claimable after P6-2 ships |

---

## Sequenced Work Queue

Items ordered by dependency and HHH criticality:

| # | Item | Phase | Status | HHH Gap Closed | Effort |
|---|---|---|---|---|---|
| ✅ | R4-1: Stroke ESI 1 calibration | 4 | Done | Helpful (ESI) · Harmless (disposition) | 30 min |
| ✅ | Guardrail system (2-layer) | 4 | Done | Harmless (input safety) | — |
| ✅ | Clinical action constraints | 4 | Done | Harmless (drug/dosage safety) | — |
| 1 | R4-4: PII scope — remove name/MRN from Supabase upsert | 4 | ❌ Open | Harmless (PII) | 15 min |
| 2 | R4-2: Stroke RAG source fix (expand stroke docs) | 4 | ❌ Open | Helpful (recall ≥ 98%) · Honest (source) | 45 min |
| 3 | R4-3: Consistency test | 4 | ⬜ Not run | Honest (consistency) | 20 min |
| 4 | P5-1: Observability dashboard | 5 | ⏳ Not started | Honest (auditability) | 2-3 hr |
| 5 | P5-2: Nurse field modification capture | 5 | ⚠️ Partial | Harmless (override audit) | 1 hr |
| 6 | P5-4: Validator agent | 5 | ⏳ Not started | Harmless (action verification) | 3-4 hr |
| 7 | P5-6: Audio-to-text intake capture | 5 | ⏳ Not started | — | 3-4 hr |
| 8 | P5-3: Multi-turn interaction | 5 | ⏳ Not started | — | ~1 wk |
| 9 | P5-5: Queue intelligence | 5 | ⏳ Not started | — | 2 hr |
| 10 | P6-1: Prior visit history (internal Supabase) | 6 | ⏳ Not started | Helpful (longitudinal context) | 4-6 hr |
| 11 | P6-2: External EHR integration (FHIR R4) | 6 | ⏳ Not started | Helpful · Harmless (allergy conflict) | 2-3 wk |
| 12 | Phase 7: Portfolio wrap-up | 7 | ⏳ Not started | — | 1-2 days |

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
