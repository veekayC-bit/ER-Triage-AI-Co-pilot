# ER Triage AI Co-pilot
**Author:** Venkat Krishnan Chellappa
**Date:** May 28, 2026
**Status:** Draft — Solution Review

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

## 4. Solution

### What we are building (V1 MVP)

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
2. As nurse types the chief complaint (free text), AI parses in real-time and populates a "Suggested structured fields" panel in the sidebar.
3. If a critical flag pattern is detected, an alert card appears in the sidebar — showing the flag, the confidence level, and the source text that triggered it (citation required, no black-box alerts).
4. Nurse reviews flagged alerts and structured suggestions. One tap to accept, one tap to dismiss. Dismissed alerts are logged with a dismissal reason (free text optional).
5. Nurse completes intake. No AI-suggested content enters the EMR record without an explicit nurse acceptance action.
6. Queue priority panel (read-only) shows current waiting room acuity distribution — updated as intakes complete.

### Key interactions and states

| State | AI Behaviour | Nurse Action Required |
|---|---|---|
| Chief complaint being typed | Real-time parsing, structured field suggestions appear | Review and accept/dismiss each suggested field |
| Critical flag detected (≥ 70% confidence) | Alert card surfaces in sidebar with source citation | Acknowledge alert (accept or dismiss with reason) |
| Critical flag detected (≥ 90% confidence) | Alert card + urgency indicator (visual + audio) | Same — nurse confirms |
| Vitals entered | AI cross-references vitals against chief complaint flags | None — passive synthesis, no new action required |
| Intake complete | Pre-populated summary shown for review | Final review and submission — nurse signs off |
| EMR integration failure | System drops to manual mode silently; nurse continues uninterrupted | None — no data loss |

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

## 5. Non-Goals (V1)

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

## 8. Open Questions

| Question | Owner | Due |
|---|---|---|
| What is the baseline intake documentation time and flag miss rate at the pilot site? | Clinical Partnerships | Before Phase 1 build |
| Does the intended use statement trigger FDA SaMD Class I or Class II classification? | Legal / Regulatory Counsel | Before Phase 2 sign-off |
| How are paediatric flag thresholds different from adult norms? | Clinical Advisory Board | Before Phase 0 shadow mode |
| What is the translation / language barrier handling strategy for non-English chief complaints? | Engineering | Before Phase 1 launch |
| Which EMR system(s) does the pilot site use, and what is the read integration scope? | Engineering / Clinical Partnerships | Before Phase 0 |
| What demographic breakdown does the pilot site's patient population have? (Bias audit prerequisite) | Clinical Partnerships | Before Phase 0 |

---

> ⚠️ *This PRD reflects the V1 MVP scope recommended following the AI Phase Assessment (May 28, 2026). The full vision includes queue state reasoning, escalation coordination, and waiting room monitoring — these are explicitly scoped to V2 and V3 to ensure V1 can be validated clinically and cleared regulatorily before expanding capability.*
