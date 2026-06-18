# ER Triage AI Co-pilot
**Author:** Venkat Krishnan Chellappa
**Date:** May 28, 2026
**Last Updated:** June 18, 2026
**Status:** Draft — In Build (Phase 4 Active)

---

## 1. Hypothesis

We believe that surfacing AI-generated critical flag alerts and structured intake suggestions to ER triage nurses — with mandatory nurse confirmation before any clinical record is updated — will reduce missed or delayed critical flags by 30% and cut documentation time per patient by 25%, measured over a 90-day shadow-mode deployment at a single ER site.

---

## 2. Problem

**Who:** ER triage nurses at high-volume emergency departments (50–200+ assessments per shift). These nurses own rapid intake assessment, acuity assignment, escalation coordination, queue prioritization, and waiting room monitoring — simultaneously, under sustained cognitive load.

**How bad:** Emergency departments face compounding operational stress: rising patient volumes, staffing shortages, documentation burden, and cognitive fatigue during peak hours.

- ED overcrowding is a documented contributor to delayed care and elevated clinical risk.
- Administrative and documentation tasks are a primary driver of nurse burnout.
- Triage inconsistency — particularly under peak volume — affects patient prioritization and escalation timing.
- High-volume shifts increase the likelihood of cognitive error on any single intake.

**What they do today:** Nurses manually synthesize structured vitals, free-text chief complaints, and physical documents (referral letters, medication lists, photo ID) to produce a triage priority and flag set. There is no AI-assisted synthesis, no real-time flag detection, and no cross-patient queue reasoning layer. Workarounds are informal: experienced nurses develop mental heuristics; newer nurses rely on colleagues during busy periods.

**If we don't solve it:** Critical flags — stroke, anaphylaxis, sepsis, suicidal ideation — continue to be at risk of delayed detection during peak volume. Nurse burnout accelerates attrition in an already understaffed domain.

**Evidence gaps:** `[NEED: site-specific data on triage completion time, flag miss rate, and nurse override behaviour from pilot partner — Owner: Clinical Partnerships, due before Phase 2 build]`

---

## 3. Strategic Fit

**Why now:** Clinical NLP has reached the reliability threshold needed for ER intake synthesis. FDA has published clearer SaMD guidance, making the regulatory pathway navigable. Healthcare AI adoption is accelerating post-2024, and nursing staff shortages make operational AI assistance a procurement priority rather than a nice-to-have.

**Why this approach:** We are not building another documentation copilot. The existing market is saturated with note-generation tools that operate in isolation. This product focuses on workflow orchestration and operational reasoning — continuous synthesis across chief complaint, vitals, queue state, escalation logic, and symptom patterns simultaneously. That is the gap.

**Why not a rules engine:** Rules-based triage decision support exists (ESI protocol software, sepsis screening alerts). These tools fire on structured thresholds — they cannot reason across free-text chief complaints, unstructured nurse notes, or the combined signal of multiple soft indicators that individually fall below a hard threshold. The clinical value is in the synthesis, not the threshold.

**Alternatives considered:**
- *Full autonomous triage scoring:* Rejected. Human judgment is required on all clinical acuity decisions. Autonomous scoring creates FDA Class II SaMD exposure and patient safety liability before we have sufficient validation data.
- *Documentation-only copilot:* Rejected. Documentation assistance alone does not address the critical flag miss risk that is the core patient safety problem.

---

## 4. Solution Vision

### End-State Product Vision

The long-term vision is an AI-powered Emergency Department Operations Copilot that assists triage nurses by identifying critical conditions, reducing documentation burden, synthesizing clinical context, and improving operational awareness while preserving clinician ownership of all medical decisions.

The product will be delivered incrementally through multiple MVP stages. The workflow and capabilities described below represent the intended end-state experience, while the Product Roadmap & Capability Evolution section defines the phased delivery plan.

A real-time AI assistance layer that runs alongside the existing triage workflow. The system surfaces structured suggestions and critical flag alerts in a sidebar — visible to the nurse during intake — and requires explicit nurse confirmation before anything enters the clinical record.

**AI owns:**
- Free-text chief complaint → structured field suggestions
- Critical flag detection across the following 10 conditions: stroke symptoms, acute MI, anaphylaxis, sepsis indicators, respiratory distress, suicidal ideation, major trauma, hypertensive crisis, altered mental status, anaphylactoid reaction
- Confidence-gated alert surfacing (alert surfaces if confidence ≥ 70%; urgency indicator escalates if ≥ 90%)
- Documentation pre-population for nurse review (shown as "suggested" — never auto-submitted)

**Nurse owns (non-negotiable):**
- Final triage acuity score / ESI assignment
- All clinical judgment on ambiguous or borderline presentations
- Confirmation of every AI-suggested field before it enters the record
- Patient interaction, physical assessment, escalation decisions

### User flow

1. Nurse opens intake screen for a new patient.
2. Nurse enters the chief complaint by typing or by using the voice capture button (microphone icon). Voice input transcribes in real-time via speech-to-text and populates the complaint text field — nurse reviews transcript before analysis fires. AI parses the complaint and populates a "Suggested structured fields" panel in the sidebar.
3. If the patient has prior visits on record, a "Prior Visits" context panel appears above the AI assessment — showing the last 1–3 encounters: date, ESI level, primary flag, and disposition. No nurse action required; it is informational context only.
4. If an external EHR connection is available, active medications, known allergies, and relevant diagnoses are surfaced alongside the AI assessment. The system flags any conflict between AI-recommended treatment and a known patient allergy before the nurse reviews.
5. If a critical flag pattern is detected, an alert card appears in the sidebar — showing the flag, the confidence level, and the source text that triggered it (citation required, no black-box alerts).
6. Nurse reviews flagged alerts and structured suggestions. One tap to accept, one tap to dismiss. Dismissed alerts are logged with a dismissal reason (free text optional).
7. Nurse completes intake. No AI-suggested content enters the EMR record without an explicit nurse acceptance action.
8. Queue priority panel (read-only) shows current waiting room acuity distribution — updated as intakes complete.

### Key interactions and states

| State | AI Behaviour | Nurse Action Required |
|---|---|---|
| Chief complaint being typed | Real-time parsing, structured field suggestions appear | Review and accept/dismiss each suggested field |
| Voice capture active | Speech-to-text transcribes in real-time into complaint field; no analysis until nurse submits | Review transcript for accuracy before triggering AI analysis |
| Prior visit history loaded | Prior visits panel (last 1–3 encounters: date, ESI, flag, disposition) displayed above AI assessment | None — read-only informational context |
| EHR context loaded | Active medications, allergies, conditions injected into AI prompt; allergy conflict surfaced if AI recommendation conflicts | Review allergy conflict flag if present — nurse confirms or overrides |
| Critical flag detected (≥ 70% confidence) | Alert card surfaces in sidebar with source citation | Acknowledge alert (accept or dismiss with reason) |
| Critical flag detected (≥ 90% confidence) | Alert card + urgency indicator (visual + audio) | Same — nurse confirms |
| Vitals entered | AI cross-references vitals against chief complaint flags | None — passive synthesis, no new action required |
| Intake complete | Pre-populated summary shown for review | Final review and submission — nurse signs off |
| EMR integration failure | System drops to manual mode silently; nurse continues uninterrupted | None — no data loss |
| EHR / prior history fetch failure | Assessment proceeds without patient history context; nurse sees "History unavailable" indicator | None — no blocking; nurse continues with complaint-only assessment |

### AI behaviour examples (input → expected output)

| Chief complaint input | AI structured output | Flag triggered? |
|---|---|---|
| "Patient says chest tightness and left arm pain for 20 min, started at rest" | Chief complaint: chest pain / left arm radiation; Onset: acute (20 min); Context: at rest | ⚠️ Acute MI indicator — confidence 91% |
| "Came in confused, family says she was fine this morning, slurring her words" | Chief complaint: acute confusion, dysarthria; Onset: acute; Witness: family | ⚠️ Stroke indicator — confidence 88% |
| "Bee sting about 5 minutes ago, throat feels tight" | Chief complaint: insect sting; Symptom: throat tightness; Onset: acute (5 min) | 🔴 Anaphylaxis — confidence 96% |
| "Feeling dizzy for 2 days, not eating well" | Chief complaint: dizziness; Duration: 2 days; Associated: poor intake | No critical flag |
| "Cut on hand from kitchen accident, bleeding controlled" | Chief complaint: laceration, hand; Bleeding status: controlled | No critical flag |
| "Says he wants to hurt himself, was brought in by police" | Chief complaint: self-harm ideation; Context: police-accompanied | ⚠️ Suicidal ideation — confidence 97% |
| "Rash spreading on torso, started 3 hours ago after new medication" | Chief complaint: rash; Onset: 3 hrs; Context: new medication | ⚠️ Possible allergic reaction — confidence 72% |
| "Shortness of breath, oxygen reading at home was 88%" | Chief complaint: dyspnea; SpO2 reported: 88%; Source: home reading | ⚠️ Respiratory distress — confidence 85% |

**Rejection criteria:** AI does not surface a flag if confidence < 70%. AI never overwrites a field the nurse has already manually confirmed. AI never auto-submits any field to the EMR. If free-text input is ambiguous or too short to parse reliably, AI shows "Insufficient detail to suggest" rather than a low-confidence guess.

**Edge case handling:**
- Non-English chief complaint: system flags language barrier for nurse, does not attempt to parse — `[NEED: translation integration decision — Owner: Eng, due before launch]`
- Paediatric patients: flag thresholds differ from adult norms — `[NEED: paediatric clinical review of flag logic — Owner: Clinical Advisory Board]`
- Nurse manually enters a value that conflicts with AI suggestion: AI suggestion is silently dropped; nurse input takes precedence

---

## 5. MVP 1 Scope — Critical Flag Detection Assistant

### Objective

Validate that AI can reliably identify high-risk patient presentations from chief complaints before introducing workflow changes or documentation assistance.

### Problem Solved

Critical conditions may be missed or recognized late during periods of high triage volume and cognitive load. Before integrating AI into clinical workflows, the system must demonstrate that it can reliably identify clinically significant presentations.

### Included Scope

#### Clinical Input Processing

- Free-text chief complaint ingestion
- Real-time NLP extraction
- Structured internal representation for model evaluation

#### Data Requirements

##### Objective

Provide the historical clinical data required to train, validate, benchmark, and continuously evaluate critical flag detection performance before any live deployment.

##### Required Data Sources

MVP 1 requires access to historical de-identified triage data from one or more pilot hospitals.

Required fields:

- Chief complaint
- Nurse intake notes (if available)
- Patient demographics (age range, gender)
- Triage acuity level (if available)
- Vitals captured during intake (if available)
- Escalation events
- Final diagnosis
- Hospital disposition outcome (admit, discharge, transfer)
- Time-to-provider metrics (if available)

##### Minimum Dataset Requirements

- 5,000+ historical triage encounters
- Minimum 500 confirmed positive cases across:
  - Stroke
  - Acute Myocardial Infarction (MI)
  - Anaphylaxis
- Representative mix of low, medium, and high acuity presentations
- Confirmed diagnosis outcomes for ground-truth validation

##### Accepted Data Delivery Formats

- CSV exports
- FHIR exports
- HL7 feeds
- De-identified database extracts

##### Data Usage

- Prompt development
- Rule development
- Model benchmarking
- Recall measurement
- Precision measurement
- False positive analysis
- Clinical review workflows
- Shadow-mode evaluation

##### Ground Truth Definition

Ground truth will be established using:

- Final diagnosis codes
- Escalation actions
- Clinical review panel validation

Ground truth data will be used to compare AI predictions against actual clinical outcomes.

##### Explicitly Not Required for MVP 1

- EMR write-back integration
- Documentation generation
- Workflow automation
- Triage recommendations
- Clinical decision automation
- Ambient audio capture

#### Critical Flag Detection

Initial conditions supported:

- Stroke
- Acute Myocardial Infarction (MI)
- Anaphylaxis

#### AI Outputs

- Critical flag prediction
- Confidence score
- Evidence citation from source text
- Audit trail for all predictions

#### Validation Infrastructure

- Shadow-mode deployment
- Clinical review dashboard
- Alert logging
- Outcome comparison reporting
- Recall and precision measurement

### Excluded Scope

- Nurse-facing alerts
- Structured field suggestions
- Documentation assistance
- Intake summaries
- Queue dashboards
- EMR integrations
- Translation support
- Medication extraction
- Referral letter processing
- Paediatric-specific logic
- Workflow recommendations

### User Experience

The AI operates in two stages: Offline Validation and Live Shadow Mode.

#### Stage 1 — Offline Validation

Historical triage records are analyzed and AI predictions are compared against confirmed clinical outcomes.

Purpose:

- Establish baseline recall
- Establish baseline precision
- Validate critical flag detection logic

#### Stage 2 — Live Shadow Mode

The system evaluates incoming triage data in parallel with existing workflows but does not surface outputs to nurses.

Purpose:

- Validate real-world performance
- Measure model drift from historical validation
- Collect clinician feedback

Nurses do not see AI output.

The system evaluates chief complaints in parallel with existing workflows and records:

- Alerts generated
- Confidence scores
- Supporting evidence
- Comparison against actual triage outcomes

No workflow changes occur during MVP 1.

### Success Criteria

- Recall ≥ 98% on validated positive cases
- Precision ≥ 85%
- 500+ reviewed shadow-mode cases
- Clinical review panel approval
- No patient safety concerns identified

### MVP 1 Non-Goals

- **NOT building full triage acuity scoring.** AI never assigns an ESI score. That is the nurse's clinical judgment. The product surfaces information; it does not decide.
- **NOT building Outlook, Epic, or Cerner write access in V1.** EMR integration in V1 is read-only for context display; writes require the nurse's explicit submit action through the existing EMR workflow.
- **NOT building vitals capture hardware integration.** Vitals are manually entered by the nurse; V1 does not pull from connected devices.
- **NOT building queue optimisation or staffing recommendations.** The queue panel is informational (read-only acuity distribution). Autonomous queue management is V3+.
- **NOT building medication tracking or prescription ingestion.** Document ingestion (referral letters, medication lists) is Phase 2.
- **NOT replacing the ESI triage protocol.** This product augments nurse judgment; it does not supersede or replace any existing clinical protocol.

---

## 6. Success Metrics

| Metric | Type | Baseline | Target | Timeframe |
|---|---|---|---|---|
| Critical flag recall (stroke, MI, anaphylaxis, sepsis, suicidal ideation) | Primary | Manual — `[NEED: baseline miss rate from pilot partner]` | ≥ 98% detection on known-positive cases | Pre-launch validation |
| Documentation time per patient intake | Primary | `[NEED: baseline timing from pilot site]` | 25% reduction vs manual baseline | 90 days post-launch |
| Nurse alert override rate | Secondary | N/A (new metric) | < 20% on documentation suggestions | 90 days post-launch |
| False positive rate on critical flags | Secondary | N/A | < 15% (i.e., precision ≥ 85% on flagged alerts) | 90 days post-launch |
| Nurse satisfaction score (system usability) | Secondary | N/A | ≥ 4.0 / 5.0 on SUS scale | 30 days post-launch |

**Guardrails (must not worsen):**
- Intake screen load time: < 1.5s (p95)
- AI suggestion latency (from last keystroke to sidebar update): < 800ms
- EMR integration uptime: ≥ 99.5% — system falls back to manual mode if breached; no patient data loss
- Overall clinical error rate: no increase vs pre-deployment baseline (tracked by clinical partner QA team)

**Passing criteria to graduate from shadow mode:** Critical flag recall ≥ 98% on 500+ validated cases reviewed by clinical panel AND no guardrail violations over 30 consecutive days.

---

## 7. Rollout Plan

**Phase 0 — Shadow mode (weeks 1–4):**
AI runs in parallel with the full manual workflow. Nurse sees nothing. System logs every suggestion and flag it would have surfaced. Clinical panel reviews AI outputs against actual nurse decisions and patient outcomes. No impact on live workflow. Go/no-go gate: recall ≥ 98% on validated set.

**Phase 1 — Limited rollout (weeks 5–8), 1 unit / 1 shift:**
Deploy to a single triage unit on a single shift. Nurse sees the sidebar. All suggestions require explicit confirmation. Override rate and satisfaction data collected daily. Go/no-go gate: no guardrail violations, override rate < 30%.

**Phase 2 — Site rollout (weeks 9–12):**
Expand to full site (all triage units, all shifts). Override rate threshold tightens to < 20%. Monitor for distribution shift (new presentation patterns not in training data).

**Phase 3 — Multi-site (post 90 days):**
Second pilot site onboarded. Per-facility protocol configuration required. Regulatory pathway decision finalised before Phase 3 begins.

**Rollback plan:** System is additive — removing it reverts nurses to the existing manual workflow with zero data loss. Rollback is a configuration flag, not a deployment event. Rollback trigger: any guardrail violation OR clinical partner escalation citing patient safety concern.

**Regulatory note:** If AI outputs influence triage priority decisions, this likely classifies as FDA SaMD (potentially Class II, 510(k) pathway). Regulatory counsel must confirm classification before Phase 3. V1 is scoped as a decision-support tool (nurse decides) to maintain the lowest feasible classification. `[NEED: healthcare regulatory counsel engagement — Owner: Legal / Clinical Partnerships, due before Phase 2 sign-off]`

---

## 8. Product Roadmap & Capability Evolution

The product will be delivered incrementally to reduce clinical, regulatory, and operational risk. Each milestone provides independently measurable value and must be validated before additional capabilities are introduced.

Roadmap Summary

- MVP 1 → Critical Flag Detection Assistant
- MVP 2 → Nurse Alert Copilot
- MVP 3A → Structured Documentation Assistant (includes intake voice capture)
- MVP 3B → Ambient Documentation Assistant (full nurse-patient conversation capture)
- MVP 4 → Operational Awareness Dashboard
- V2 → Clinical Context Expansion (prior visit history + external EHR via FHIR R4)
- V3 → Emergency Department Operations Copilot

### MVP 1 — Critical Flag Detection Assistant

**Goal:** Validate that AI can reliably identify high-risk patient presentations from chief complaints.

#### Scope

- Free-text chief complaint ingestion
- Detection of:
  - Stroke
  - Acute MI
  - Anaphylaxis
- Confidence scoring
- Evidence citation
- Audit logging
- Shadow-mode deployment
- Clinical review dashboard

#### Data Prerequisites

- Access to de-identified historical triage records
- Confirmed diagnosis outcomes
- Minimum 5,000 encounters
- Representative positive cases for Stroke, MI, and Anaphylaxis
- Clinical review panel for ground-truth verification

#### Key Question

Can AI reliably detect clinically significant presentations from chief complaints?

#### Exit Criteria

- Recall ≥ 98%
- Precision ≥ 85%
- 500+ validated cases
- Clinical review approval

### MVP 2 — Nurse Alert Copilot

**Goal:** Introduce explainable AI alerts into the nurse workflow.

#### Added Capabilities

Everything in MVP 1 plus:

- Real-time alert sidebar
- Nurse alert acknowledgement workflow
- Alert dismissal reasons
- Audit trail of nurse interactions
- Urgency indicators for high-confidence alerts
- Vitals consistency check — flags vitals that cross critical thresholds but aren't explained by the chief complaint text; nurse reviews or dismisses as expected

#### Expanded Clinical Coverage

Adds:

- Sepsis
- Respiratory Distress
- Suicidal Ideation
- Major Trauma
- Hypertensive Crisis
- Altered Mental Status
- Anaphylactoid Reaction

#### Key Question

Will nurses trust and appropriately act on AI-generated alerts?

#### Exit Criteria

- Alert override rate < 30%
- Nurse satisfaction ≥ 4.0 / 5.0
- No increase in triage completion time
- No safety incidents attributable to the system

#### Future Enhancement — Quality Control Layer (post-MVP 2, not yet scoped)

As clinical coverage expands, consider a second-pass verifier/critic agent that audits the primary flag-detection model's output (flag type, confidence, vitals consistency) against source text and clinical thresholds before it reaches the nurse — a generator + verifier multi-agent pattern aimed at reducing false negatives/positives on the monitored conditions. Tradeoff: roughly doubles per-case latency and OpenAI cost. Not required for MVP 1/2; revisit once shadow-mode data shows where the single-pass model's errors cluster.

### MVP 3A — Structured Documentation Assistant

**Goal:** Reduce triage documentation burden through AI-assisted structured data extraction while preserving nurse ownership.

#### Objective

Automatically extract structured clinical information from nurse-entered text and pre-populate documentation fields for review.

#### Workflow

Nurse Types Chief Complaint
↓
Clinical Extraction Engine
↓
Structured Field Suggestions
↓
Documentation Pre-Population
↓
Nurse Review & Approval

#### Added Capabilities

Everything in MVP 2 plus:

- Structured field suggestions
- Symptom extraction
- Duration extraction
- Onset extraction
- Context extraction
- Documentation pre-population
- Nurse review and approval workflow
- **Intake voice capture:** Nurse dictates the chief complaint by voice; speech-to-text (OpenAI Whisper) transcribes into the complaint field. Nurse reviews and edits the transcript before triggering AI analysis. This is complaint-entry voice capture only — not full ambient room audio. Requires nurse consent to use microphone. Fallback to typed entry if mic unavailable or denied.

#### Example

Input:

"Patient reports chest tightness and left arm pain that started 20 minutes ago while resting at home."

AI Extracts:

- Chief Complaint: Chest Pain
- Symptom: Left Arm Pain
- Duration: 20 Minutes
- Onset: Acute
- Context: At Rest

Pre-Populated Form:

- Chief Complaint: Chest Pain
- Symptoms: Left Arm Pain
- Duration: 20 Minutes
- Onset: Acute
- Context: At Rest

Status: AI Suggested — Nurse Review Required

#### Key Question

Can AI reduce documentation effort through structured extraction while maintaining clinical accuracy?

#### Exit Criteria

- Documentation time reduced by 20%
- Structured extraction accuracy > 90%
- Suggestion acceptance rate > 60%

### MVP 3B — Ambient Documentation Assistant

**Goal:** Capture the full nurse-patient conversation in real time and convert it into structured clinical documentation.

**Distinction from MVP 3A voice capture:** MVP 3A voice capture is nurse-dictated intake only — the nurse speaks a brief complaint summary into the mic. MVP 3B captures the full clinical dialogue between nurse and patient in the room: multi-turn conversation, speaker identification, medical history elicitation, symptom exploration. Significantly higher complexity, latency, and consent requirements.

#### Objective

Generate transcripts, extract clinical information, and pre-populate documentation with minimal manual typing.

#### Workflow

Nurse + Patient Conversation
↓
Speech-to-Text
↓
Clinical Extraction Engine
↓
Structured Documentation
↓
Nurse Review & Approval

#### Added Capabilities

Everything in MVP 3A plus:

- Real-time speech-to-text
- Speaker identification (nurse vs patient)
- Timestamped transcript generation
- Conversation-to-documentation extraction
- Intake summary generation
- Transcript review and correction workflow

#### Example

Conversation:

Nurse: "What brings you in today?"

Patient: "My chest feels tight and the pain is going down my left arm."

Nurse: "When did this start?"

Patient: "About 20 minutes ago."

AI Extracts:

- Chief Complaint: Chest Pain
- Symptom: Left Arm Pain
- Duration: 20 Minutes
- Onset: Acute

Generated Intake Summary:

- Chief Complaint: Chest Pain
- Associated Symptoms: Left Arm Pain
- Duration: 20 Minutes
- Potential Concern: Acute MI
- Nurse Review: Pending Approval

#### Additional Requirements

- HIPAA-compliant audio storage
- Audio retention policy
- Medical terminology recognition
- Background noise handling
- Audio consent workflow

#### Key Question

Can ambient documentation significantly reduce documentation burden while maintaining accuracy and clinician trust?

#### Exit Criteria

- Speech recognition accuracy > 95%
- Medical terminology accuracy > 90%
- End-to-end latency < 2 seconds
- Documentation time reduced by 40%
- Nurse satisfaction ≥ 4.0 / 5.0

### MVP 4 — Operational Awareness Dashboard

**Goal:** Improve situational awareness for triage and charge nurses.

#### Added Capabilities

Everything in MVP 3A and MVP 3B plus:

- Queue distribution dashboard
- Waiting room acuity visualization
- Shift-level operational metrics
- Read-only operational monitoring dashboard

#### Explicitly Excluded

- Queue prioritization
- Staffing recommendations
- Automated escalation
- Autonomous workflow decisions

#### Key Question

Does operational visibility improve awareness during peak-volume periods?

#### Exit Criteria

- Active usage by triage leadership
- Positive operational feedback from pilot site

### V2 — Clinical Context Expansion

**Goal:** Expand the quality and breadth of clinical context available to the AI system so that AI assessments reflect the full patient picture, not just the presenting complaint.

V2 introduces two distinct patient context layers delivered in sequence: internal visit history first (lower risk, no external dependency), then external EHR integration.

#### V2a — Prior Visit History (Internal)

Pulls the patient's prior encounters from the system's own database and injects them into the triage assessment before classification runs.

**What is surfaced:**
- Last 1–3 encounters: visit date, ESI level, primary flag detected, nurse disposition, nurse action (accepted/dismissed/edited)
- Presented as read-only context panel above the AI assessment — nurse sees it, not injected silently

**Why it matters clinically:**
A patient presenting with chest pain who was discharged ESI 3 two weeks ago for the same complaint is a different risk profile from a first-time presenter. A patient with three prior high-acuity sepsis presentations warrants faster escalation. Without history, the AI treats every visit as a cold start.

**Implementation requirements:**
- Patient lookup key: hashed MRN (SHA-256) — plaintext MRN must not be stored
- Supabase query on `encounters` table: last 3 rows matching hashed MRN, ordered by `created_at DESC`
- Injected into AI classification prompt as structured context block (not free text)
- If no prior encounters: field omitted from prompt — no hallucinated history
- Latency target: < 200ms (single indexed query)

**Prerequisite:** PII scope must be resolved before this feature ships — MRN must be stored as a hash, not plaintext.

#### V2b — External EHR Integration (FHIR R4)

Connects to the patient's external EHR system via HL7 FHIR R4 API to retrieve their full active clinical record at intake time and inject it into the triage assessment.

**Why it matters clinically:**
- A patient on warfarin presenting with head trauma is ESI 1, not ESI 2.
- A patient allergic to aspirin where the AI recommends aspirin for chest pain is a Harmless failure.
- Chronic CHF presenting with dyspnea has a different workup than a first-time presenter.
- A troponin result from 6 hours ago at another facility changes the entire chest pain workup.

**FHIR resources pulled:**
- `Patient/{id}` — demographics confirmation (age, gender)
- `MedicationRequest?patient={id}&status=active` — current active medications
- `AllergyIntolerance?patient={id}` — documented allergies and intolerances
- `Condition?patient={id}&clinical-status=active` — active diagnoses
- `Observation?patient={id}&category=laboratory&_sort=-date&_count=5` — 5 most recent labs

**Allergy conflict guard:**
The AI assessment prompt includes an explicit instruction: if any recommended treatment (medication, intervention) conflicts with a known allergy in the FHIR record, flag it as `ALLERGY CONFLICT: [drug] — [allergy/intolerance]` in the clinical notes field. This surfaces to the nurse before she accepts the recommendation.

**Implementation constraints:**
- Read-only. No write-back to external EHR in V2.
- FHIR data is in-flight only — used for the current encounter prompt, never persisted to the system database.
- Graceful degradation: if the FHIR call fails or times out (> 2s), the assessment proceeds without EHR context. Nurse sees "EHR context unavailable" indicator.
- Integration target for portfolio/pilot build: SMART on FHIR sandbox (Epic or HAPI FHIR public test server). Production deployment requires formal EHR vendor agreement and OAuth SMART authorization.

#### V2 — Additional Capabilities (carried forward)

- Referral letter ingestion (OCR + document processing)
- Medication list extraction from physical documents
- Translation support and multi-language intake assistance
- Paediatric-specific flag logic and threshold adjustment
- Additional critical condition coverage beyond the initial 10

### V3 — Emergency Department Operations Copilot

**Goal:** Transform from patient-level assistance to department-level operational intelligence.

#### Added Capabilities

- Queue state reasoning
- Escalation coordination recommendations
- Waiting room monitoring
- Risk trend identification
- Operational bottleneck detection
- Multi-site deployment support
- Cross-site benchmarking and analytics

### Long-Term Vision

An AI-powered Emergency Department Operations Copilot that continuously assists triage nurses by identifying critical conditions, reducing documentation burden, synthesizing clinical context, and improving situational awareness while preserving clinician ownership of all medical decisions.

---

## 9. Open Questions

| Question | Owner | Due |
|---|---|---|
| What is the baseline intake documentation time and flag miss rate at the pilot site? | Clinical Partnerships | Before Phase 1 build |
| What historical triage dataset is available for model training and validation (volume, fields, diagnosis outcomes)? | Clinical Partnerships | Before MVP 1 build |
| Does the intended use statement trigger FDA SaMD Class I or Class II classification? | Legal / Regulatory Counsel | Before Phase 2 sign-off |
| How are paediatric flag thresholds different from adult norms? | Clinical Advisory Board | Before Phase 0 shadow mode |
| What is the translation / language barrier handling strategy for non-English chief complaints? | Engineering | Before Phase 1 launch |
| Which EMR system(s) does the pilot site use, and what is the read integration scope? | Engineering / Clinical Partnerships | Before Phase 0 |
| What demographic breakdown does the pilot site's patient population have? (Bias audit prerequisite) | Clinical Partnerships | Before Phase 0 |
| **Voice capture:** Does the pilot site's device environment support browser-based microphone access? What is the policy on nurse-facing audio input at intake stations? | Clinical Partnerships / IT | Before MVP 3A voice capture build |
| **Voice capture:** Does nurse-dictated complaint audio require HIPAA-compliant handling even if it is not retained? If audio is processed in-flight by a third-party STT API (e.g., OpenAI Whisper), does that require a BAA? | Legal / Compliance | Before MVP 3A voice capture build |
| **Prior visit history:** Is a hashed MRN (SHA-256) sufficient as a patient lookup key for cross-encounter linking, or does the site require a HIPAA-compliant patient identifier beyond a hash? | Legal / Clinical Partnerships | Before V2a build |
| **Prior visit history:** What is the retention policy for encounter data in the system's internal database? How long should prior visits be surfaced in the context panel? | Clinical Partnerships | Before V2a build |
| **FHIR R4 integration:** Which FHIR server does the target pilot site expose? Does it support SMART on FHIR authorization, or will a separate integration agreement be required? | Engineering / Clinical Partnerships | Before V2b build |
| **FHIR R4 integration:** What is the acceptable latency ceiling for the FHIR context fetch before it blocks the nurse's intake workflow? (Current assumption: 2s timeout, degrade gracefully.) | Clinical Partnerships | Before V2b design sign-off |
| **FHIR R4 integration:** Who is the clinical reviewer for the allergy conflict guard logic? What categories of drug-allergy conflicts should be flagged vs. surfaced as informational only? | Clinical Advisory Board | Before V2b build |

---

> ⚠️ *This PRD reflects the V1 MVP scope recommended following the AI Phase Assessment (May 28, 2026). The full vision includes queue state reasoning, escalation coordination, and waiting room monitoring — these are explicitly scoped to V2 and V3 to ensure V1 can be validated clinically and cleared regulatorily before expanding capability.*
